#!/usr/bin/env python3
"""Build and verify in a fresh Ubuntu Base rootfs using unprivileged bubblewrap."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

BASE_NAME = 'ubuntu-base-24.04.5-base-amd64.tar.gz'
BASE_URL = 'https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/' + BASE_NAME
BASE_SHA256 = 'e77b6f10c2590cef872b33ee9f635a0e3fd1f57fb074c0e52b5c7f56147a0c86'
SOURCE = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    """Return the streaming SHA-256 of an input artifact."""
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path: Path, value: object) -> None:
    """Atomically persist a process checkpoint."""
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def write_progress(path: Path, report: dict) -> None:
    """Maintain a readable process record alongside every JSON checkpoint."""
    local_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    lines = ['# 零环境部署过程记录', '', '更新时间：' + local_time + '（Asia/Shanghai）', '',
             '- 源码：`' + report['source'] + '`',
             '- 环境：`' + report['directory'] + '`',
             '- 基础镜像：' + report['base_url'],
             '- SHA-256：`' + report['base_sha256'] + '`', '',
             '## 当前阶段', '', '| 阶段 | 状态 | 退出码 | 日志 |',
             '|---|---|---|---|']
    for name, stage in report.get('stages', {}).items():
        code = stage.get('exit_code')
        status = '运行中' if code is None else ('通过' if code == 0 else '失败')
        lines.append('| ' + name + ' | ' + status + ' | ' + str(code)
                     + ' | [' + Path(stage['log']).name + '](' + stage['log'] + ') |')
    lines += ['', '## 初始环境', '']
    if report.get('initial_environment'):
        initial = json.dumps(report['initial_environment'], ensure_ascii=False, indent=2)
        lines += ['```json', initial, '```']
    else:
        lines += ['尚未完成空环境断言。']
    lines += ['', '## 阶段历史', '', '| 阶段 | 开始时间（UTC） | 退出码 | 日志 |',
              '|---|---|---|---|']
    for stage in report.get('stage_history', []):
        lines.append('| ' + stage['name'] + ' | ' + stage['started_utc'] + ' | '
                     + str(stage['exit_code']) + ' | [' + Path(stage['log']).name
                     + '](' + stage['log'] + ') |')
    if report.get('error'):
        lines += ['', '当前失败原因：`' + report['error'] + '`。详细原因见对应日志。']
    lines += ['', '完整验证通过：' + str(report.get('full_validation_passed', False)),
              '', '安装与构建可联网；运行验证仅使用独立回环网络。',
              '记录共享内核的根文件系统验证，不包含真实硬件或 Gazebo 验收。', '']
    temporary = path.with_suffix('.tmp')
    temporary.write_text('\n'.join(lines))
    temporary.replace(path)


def source_ignore(directory: str, names: list[str]) -> set[str]:
    """Exclude generated dependencies while retaining vendor source assets."""
    ignored = {name for name in names if name in (
        'node_modules', '__pycache__', '.pytest_cache', '.git')}
    if Path(directory) == SOURCE / 'src/ros2_web_link':
        ignored.add('dist')
    return ignored


def copy_source(workspace: Path) -> None:
    """Copy source and the minimal fixture into an empty workspace."""
    workspace.mkdir()
    for name in ('src', 'scripts', 'docs', '.colcon'):
        if (SOURCE / name).exists():
            shutil.copytree(SOURCE / name, workspace / name, symlinks=True,
                            ignore=source_ignore)
    for name in ('AGENTS.md', 'README.md', 'README_PACKAGE.md', 'requirements.txt', 'LICENSE'):
        shutil.copy2(SOURCE / name, workspace / name)
    fixture = 'runs/data/delivery_simulation_20261106'
    shutil.copytree(SOURCE / fixture, workspace / fixture, symlinks=True)


def namespaces() -> dict[str, str]:
    """Capture namespace identifiers for isolation evidence."""
    return {name: os.readlink('/proc/self/ns/' + name)
            for name in ('user', 'mnt', 'pid', 'ipc', 'net', 'uts')}


def main() -> int:
    """Prepare an owned rootfs and execute the requested deployment stage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--base-archive', type=Path)
    parser.add_argument('--ubuntu-mirror', help='explicit HTTPS Ubuntu apt mirror')
    parser.add_argument('--ros-mirror', help='explicit HTTPS ROS 2 apt mirror')
    parser.add_argument('--stage', choices=('all', 'prepare', 'system', 'build', 'verify'),
                        default='all')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--grasp', action='store_true')
    parser.add_argument('--web-e2e', action='store_true')
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    if os.uname().machine != 'x86_64':
        parser.error('the delivered vendor binaries and this base image require amd64')
    for mirror in (args.ubuntu_mirror, args.ros_mirror):
        if mirror and (not mirror.startswith('https://') or '\n' in mirror):
            parser.error('apt mirrors must be single-line HTTPS URLs')
    if not shutil.which('bwrap'):
        parser.error('bubblewrap is required on the host (Ubuntu package: bubblewrap)')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    directory = (args.directory or SOURCE.parent / ('clean_room_' + stamp)).resolve()
    if not str(directory).isascii() or ' ' in str(directory):
        parser.error('use an ASCII directory without spaces')
    if directory == SOURCE or SOURCE.is_relative_to(directory):
        parser.error('the clean-room directory must not contain the source workspace')
    marker = directory / 'clean_room.json'
    if directory.exists():
        if not args.resume or not marker.is_file():
            parser.error('directory already exists; use a new directory or --resume')
        report = json.loads(marker.read_text())
        if report.get('schema') != 'peach-clean-room-v1':
            parser.error('not an owned clean-room directory')
    else:
        directory.mkdir(parents=True)
        report = {'schema': 'peach-clean-room-v1', 'id': uuid.uuid4().hex,
                  'started_utc': stamp, 'source': str(SOURCE), 'directory': str(directory),
                  'base_url': BASE_URL, 'base_sha256': BASE_SHA256,
                  'host_namespaces': namespaces(), 'stages': {}}
        write_json(marker, report)
    rootfs = directory / 'rootfs'
    workspace = directory / 'workspace'
    logs = directory / 'logs'
    logs.mkdir(exist_ok=True)
    selected_mirrors = report.get('apt_mirrors', {})
    args.ubuntu_mirror = args.ubuntu_mirror or selected_mirrors.get('ubuntu')
    args.ros_mirror = args.ros_mirror or selected_mirrors.get('ros')
    report.pop('error', None)
    report['requested_stage_passed'] = False
    report['full_validation_passed'] = False
    downstream = ()
    if args.stage in ('all', 'system'):
        downstream = ('build', 'browser_download', 'verify')
    elif args.stage == 'build':
        downstream = ('browser_download', 'verify')
    for name in downstream:
        report['stages'].pop(name, None)

    def save() -> None:
        """Save the current process checkpoint."""
        write_json(marker, report)
        write_progress(directory / 'process.md', report)

    def run(label: str, command: list[str]) -> None:
        """Run a stage while preserving its log and exit status."""
        attempt = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        log = logs / (label + '_' + attempt + '_' + uuid.uuid4().hex[:6] + '.log')
        stage = {'started_utc': datetime.now(timezone.utc).isoformat(),
                 'exit_code': None, 'state': 'running', 'log': str(log)}
        report['stages'][label] = stage
        save()
        print('[' + label + '] ' + str(log), flush=True)
        with log.open('w') as stream:
            process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
        stage.update(exit_code=process.returncode, state='finished',
                     finished_utc=datetime.now(timezone.utc).isoformat())
        report.setdefault('stage_history', []).append({'name': label, **stage})
        save()
        if process.returncode:
            print(log.read_text(errors='replace')[-7000:], file=sys.stderr)
            raise RuntimeError(label + ' failed (exit ' + str(process.returncode) + ')')

    def container(command: list[str], offline: bool = False) -> list[str]:
        """Construct a namespace invocation with only the owned filesystem."""
        cmd = ['bwrap', '--unshare-user', '--uid', '0', '--gid', '0', '--unshare-pid',
               '--unshare-ipc', '--unshare-uts', '--hostname', 'peach-clean-room',
               '--die-with-parent', '--new-session', '--bind', str(rootfs), '/',
               '--bind', str(workspace), '/workspace', '--proc', '/proc', '--dev', '/dev',
               '--tmpfs', '/tmp', '--tmpfs', '/run', '--chdir', '/workspace', '--clearenv',
               '--setenv', 'HOME', '/root', '--setenv', 'PATH',
               '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
               '--setenv', 'LANG', 'C.UTF-8', '--setenv', 'LC_ALL', 'C.UTF-8',
               '--setenv', 'PEACH_CLEAN_ROOM', '1', '--setenv', 'PYTHONNOUSERSITE', '1',
               '--setenv', 'PEACH_CLEAN_HOST_HOME', str(Path.home())]
        if args.ros_mirror:
            cmd += ['--setenv', 'PEACH_ROS_APT_MIRROR', args.ros_mirror]
        if offline:
            cmd += ['--unshare-net', '--cap-add', 'CAP_NET_ADMIN']
        else:
            for name in ('http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY'):
                if name in os.environ:
                    cmd += ['--setenv', name, os.environ[name]]
        return cmd + ['--', *command]

    try:
        with (logs / 'host_processes_before.txt').open('w') as stream:
            subprocess.run(['ps', '-eo', 'pid,ppid,pgid,comm'], stdout=stream, check=True)
        if not report.get('prepared'):
            archive = args.base_archive.resolve() if args.base_archive else directory / BASE_NAME
            if not archive.exists():
                run('download_base', [
                    'curl', '--fail', '--location', '--retry', '3',
                    '--connect-timeout', '20', BASE_URL, '--output', str(archive)])
            if digest(archive) != BASE_SHA256:
                raise RuntimeError('Ubuntu Base SHA-256 mismatch')
            rootfs.mkdir()
            run('extract_base', ['tar', '--extract', '--gzip', '--no-same-owner',
                                 '--file', str(archive), '--directory', str(rootfs)])
            copy_source(workspace)
            for name, content in {
                'etc/resolv.conf': Path('/etc/resolv.conf').read_text(),
                'etc/hosts': '127.0.0.1 localhost peach-clean-room\n::1 localhost\n',
                'etc/peach-clean-room': report['id'] + '\n',
                'etc/apt/apt.conf.d/99peach-rootless': (
                    'APT::Sandbox::User "root";\nAcquire::Retries "3";\n'
                    'Acquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n'),
                'usr/sbin/policy-rc.d': '#!/bin/sh\nexit 101\n',
            }.items():
                path = rootfs / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink():
                    path.unlink()
                path.write_text(content)
            (rootfs / 'usr/sbin/policy-rc.d').chmod(0o755)
            baseline = ['/bin/bash', '-ec',
                        'if test "$1" != /root; then test ! -e "$1" || exit 20; fi; '
                        'for path in /opt/ros /workspace/build /workspace/install '
                        '/workspace/aubo_py3.12 /workspace/.deps; do '
                        'test ! -e "$path" || exit 20; done; '
                        'for name in node colcon; do '
                        'if command -v "$name"; then exit 21; fi; done; '
                        'cat /etc/os-release; cat /proc/self/uid_map; '
                        'test -f /etc/peach-clean-room', 'baseline', str(Path.home())]
            run('empty_baseline', container(baseline))
            report['prepared'] = True
            report['initial_environment'] = {
                'ros': False, 'node': False, 'colcon': False, 'venv': False,
                'build_install': False, 'host_home_mounted': False,
                'host_package_caches_mounted': False,
                'source_only_fixture_copied': True,
                'namespace_root_mapping': 'container uid 0 maps to the invoking host user'}
            save()
        elif args.resume:
            if (rootfs.is_symlink() or workspace.is_symlink()
                    or (rootfs / 'etc/peach-clean-room').read_text().strip() != report['id']):
                raise RuntimeError('Clean-room ownership marker mismatch')
            # Deliver installer fixes without importing any host dependencies or artifacts.
            for path in (SOURCE / 'scripts/deployment').iterdir():
                if path.is_file():
                    shutil.copy2(path, workspace / 'scripts/deployment' / path.name)
            shutil.copy2(SOURCE / 'requirements.txt', workspace / 'requirements.txt')
        bootstrap_ca = not (rootfs / 'etc/ssl/certs/ca-certificates.crt').is_file()
        if args.ubuntu_mirror:
            sources = rootfs / 'etc/apt/sources.list'
            if sources.exists():
                sources.rename(sources.with_name('sources.list.original'))
            sources = rootfs / 'etc/apt/sources.list.d/ubuntu.sources'
            ubuntu_uri = (args.ubuntu_mirror.replace('https://', 'http://', 1)
                          if bootstrap_ca else args.ubuntu_mirror)
            sources.write_text('Types: deb\nURIs: ' + ubuntu_uri + '\n'
                               'Suites: noble noble-updates noble-security noble-backports\n'
                               'Components: main universe restricted multiverse\n'
                               'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n')
        report['apt_mirrors'] = {'ubuntu': args.ubuntu_mirror, 'ros': args.ros_mirror}
        save()
        if args.stage == 'prepare':
            return 0
        if args.stage in ('all', 'system'):
            # One uid is mapped; fakeroot emulates package ownership metadata only.
            run('bootstrap_tools', container([
                '/bin/bash', '-ec',
                'export DEBIAN_FRONTEND=noninteractive; apt-get update; '
                'if command -v fakeroot >/dev/null; then '
                'exec env FAKEROOTDONTTRYCHOWN=1 fakeroot -- apt-get '
                '-o Acquire::Retries=3 install -y --no-install-recommends '
                'fakeroot ca-certificates; '
                'else apt-get -o Acquire::Retries=3 install -y --no-install-recommends '
                'fakeroot ca-certificates; fi']))
            if args.ubuntu_mirror and bootstrap_ca:
                sources = rootfs / 'etc/apt/sources.list.d/ubuntu.sources'
                sources.write_text(sources.read_text().replace(
                    args.ubuntu_mirror.replace('https://', 'http://', 1), args.ubuntu_mirror))
                report['certificate_bootstrap'] = (
                    'Installed ca-certificates via GPG-verified apt before switching to HTTPS')
                save()
            run('system', container([
                '/usr/bin/env', 'FAKEROOTDONTTRYCHOWN=1',
                '/usr/bin/fakeroot', '--', '/bin/bash',
                '/workspace/scripts/deployment/bootstrap_ubuntu.sh', '/workspace']))
        if args.stage in ('all', 'build'):
            if report['stages'].get('system', {}).get('exit_code') != 0:
                raise RuntimeError('Complete the system stage before building')
            deployment = '/workspace/runs/clean_validation/deployment'
            if (workspace / 'runs/clean_validation/deployment').exists():
                deployment += '_' + stamp
            report['deployment_path'] = str(workspace / deployment.removeprefix('/workspace/'))
            command = ['/bin/bash', '/workspace/scripts/deployment/deploy.sh',
                       '--jobs', str(args.jobs),
                       '--output', deployment]
            run('build', container(command))
            if args.web_e2e:
                # Browser download only: runtime verification belongs to the offline stage.
                run('browser_download', container([
                    '/bin/bash', '-ec',
                    'PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright '
                    'node /workspace/src/ros2_web_link/node_modules/playwright/cli.js '
                    'install chromium']))
        if args.stage in ('all', 'verify'):
            if report['stages'].get('build', {}).get('exit_code') != 0:
                raise RuntimeError('Complete the build stage before runtime verification')
            verification = '/workspace/runs/clean_validation/verification'
            if (workspace / 'runs/clean_validation/verification').exists():
                verification += '_' + stamp
            command = ['/bin/bash', '/workspace/scripts/deployment/verify.sh',
                       '--output', verification]
            if args.grasp:
                command += ['--grasp']
            if args.web_e2e:
                command += ['--web-e2e']
            run('verify', container(['/bin/bash', '-ec',
                'ip link set lo up; exec "$@"', 'clean-verify', *command], offline=True))
            report['verification_path'] = str(workspace / verification.removeprefix('/workspace/'))
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
        report['requested_stage_passed'] = True
        report['full_validation_passed'] = all(
            report['stages'].get(name, {}).get('exit_code') == 0
            for name in ('empty_baseline', 'system', 'build', 'verify'))
        report['installer_sha256'] = {
            path.name: digest(path) for path in (SOURCE / 'scripts/deployment').iterdir()
            if path.is_file()}
        save()
        print('Clean-room stage completed: ' + str(marker), flush=True)
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        report['error'] = str(error)
        report['requested_stage_passed'] = False
        save()
        print(str(error), file=sys.stderr)
        return 1
    finally:
        with (logs / 'host_processes_after.txt').open('w') as stream:
            subprocess.run(['ps', '-eo', 'pid,ppid,pgid,comm'], stdout=stream)


if __name__ == '__main__':
    sys.exit(main())
