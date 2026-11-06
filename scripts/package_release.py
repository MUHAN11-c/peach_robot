#!/usr/bin/env python3
"""Create and check a versioned, self-contained Peach source release."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRECTORIES = {
    '.git', '.agents', '.codex', '.aws', '.cache', '.upstream', '.pytest_cache',
    '.vscode', '.idea', 'node_modules', '__pycache__', 'Testing',
}
BASELINE_REPORTS = (
    'clean_room_summary.json', 'clean_room_all_bag_reads.json',
    'clean_room_final_process_audit.json', 'clean_room_source_audit.json',
    'deployment_scripts_flake8.log', 'deployment_scripts_pep257.log',
    'test_cases_summary.json', 'test_xml_inventory.json',
)


def digest(path: Path) -> str:
    """Hash a regular file without loading large models into memory."""
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def dump(path: Path, value: object) -> None:
    """Write readable release metadata."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def skip(path: Path) -> bool:
    """Exclude generated state and explicitly optional non-Peach assets."""
    parts = path.relative_to(ROOT).parts
    if any(part in SKIP_DIRECTORIES for part in parts):
        return True
    if parts[:3] == ('src', 'ros2_web_link', 'dist'):
        return True
    if any(part in ('build', 'install', 'log') for part in parts):
        if ('web', 'public', 'build') not in tuple(zip(parts, parts[1:], parts[2:])):
            return True
    if path.name.endswith(('~', '.pyc', '.pyo', '.orig', '.partial', '.preview.png')):
        return True
    if path.name in ('.env', '.env.local', '.env.production', '.DS_Store', 'Thumbs.db'):
        return True
    optional_models = ROOT / 'src/ivg/ivg_pose_estimation/models'
    if path.parent == optional_models and path.suffix in ('.onnx', '.pt', '.pth'):
        return True
    if len(parts) > 5 and parts[:4] == ('src', 'ivg', 'ivg_sim', 'models'):
        if parts[5] == 'meshes':
            return True
    return path.name in ('field_no_grass.glb', '.dinov2_index.npz', 'mobileclip2_b.ts')


def source_files(version: str) -> list[Path]:
    """Collect explicit source, essential assets, fixtures and selected evidence."""
    roots = ['src', 'scripts', 'docs', '.colcon', 'VERSION', 'CHANGELOG.md',
             'AGENTS.md', 'LICENSE', 'README.md', 'README_PACKAGE.md',
             '.gitignore', 'requirements.txt',
             'runs/data/delivery_simulation_20261106',
             f'runs/releases/v{version}/baseline']
    reports = 'runs/analysis_reports/deployment_20261107/'
    roots.extend(reports + name for name in BASELINE_REPORTS)
    result = []

    def walk(path: Path) -> None:
        """Do not follow symlink directories or traverse generated dependencies."""
        if skip(path):
            return
        if path.is_symlink():
            target = os.readlink(path)
            if os.path.isabs(target) or not path.resolve().is_relative_to(ROOT):
                raise ValueError('External or absolute symlink: ' + str(path))
            if not path.exists():
                raise ValueError('Broken source symlink: ' + str(path))
            result.append(path)
        elif path.is_dir():
            result.append(path)
            for child in sorted(path.iterdir()):
                walk(child)
        elif path.is_file():
            result.append(path)
        else:
            raise ValueError('Missing or special release input: ' + str(path))

    for name in roots:
        walk(ROOT / name)
    files = sorted(set(result))
    selected = set(files)
    for path in files:
        if path.is_symlink() and path.resolve() not in selected:
            raise ValueError('Symlink target excluded from release: ' + str(path))
    for name in ('best.pt', 'FastSAM-s.pt', 'mobile_sam.pt'):
        if ROOT / 'src/peach/peach_scene_perception/model' / name not in selected:
            raise ValueError('Missing Peach model: ' + name)
    fixture = ROOT / 'runs/data/delivery_simulation_20261106/rgbd_frame_bag'
    if fixture / 'metadata.yaml' not in selected or not list(fixture.glob('*.mcap')):
        raise ValueError('Minimal RGB-D fixture is incomplete')
    return files


def file_record(path: Path) -> dict:
    """Describe portable file content and permissions."""
    if path.is_symlink():
        return {'type': 'symlink', 'target': os.readlink(path), 'mode': '0777'}
    if path.is_dir():
        return {'type': 'directory', 'mode': '0755'}
    return {'type': 'file', 'bytes': path.stat().st_size, 'sha256': digest(path),
            'mode': '0755' if path.stat().st_mode & 0o111 else '0644'}


def check_archive(archive: Path) -> dict:
    """Stream all archive members, rejecting missing, changed or unsafe content."""
    listed = {}
    manifest = None
    process = subprocess.Popen(['zstd', '--decompress', '--stdout', '--quiet', str(archive)],
                               stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdout, mode='r|') as stream:
            for member in stream:
                name = PurePosixPath(member.name)
                if name.is_absolute() or '..' in name.parts or len(name.parts) < 2:
                    raise ValueError('Unsafe archive path: ' + member.name)
                if member.name in listed:
                    raise ValueError('Duplicate archive member: ' + member.name)
                if member.isfile():
                    data = stream.extractfile(member)
                    if name.name == 'RELEASE_MANIFEST.json' and len(name.parts) == 2:
                        payload = data.read()
                        manifest = json.loads(payload)
                        record = {'type': 'manifest'}
                    else:
                        sha = hashlib.file_digest(data, 'sha256').hexdigest()
                        record = {'type': 'file', 'bytes': member.size, 'sha256': sha,
                                  'mode': f'{member.mode:04o}'}
                elif member.isdir():
                    record = {'type': 'directory', 'mode': f'{member.mode:04o}'}
                elif member.issym():
                    target = PurePosixPath(member.linkname)
                    if target.is_absolute():
                        raise ValueError('Absolute symlink in archive: ' + member.name)
                    resolved = list(name.parts[:-1])
                    for part in target.parts:
                        if part == '..':
                            if len(resolved) < 2:
                                raise ValueError('Escaping symlink: ' + member.name)
                            resolved.pop()
                        elif part != '.':
                            resolved.append(part)
                    record = {'type': 'symlink', 'target': member.linkname,
                              'mode': f'{member.mode:04o}'}
                else:
                    raise ValueError('Unsupported archive member: ' + member.name)
                listed[member.name] = record
        while process.stdout.read(1024 * 1024):
            pass
        if process.wait() != 0:
            raise ValueError('zstd stream check failed')
    finally:
        process.stdout.close()
        if process.poll() is None:
            process.terminate()
            process.wait()
    if not manifest or manifest.get('schema') != 'peach-source-release-v1':
        raise ValueError('Missing release manifest')
    prefix = manifest['archive_root'] + '/'
    expected = {prefix + name: row for name, row in manifest['files'].items()}
    expected[prefix + 'RELEASE_MANIFEST.json'] = {'type': 'manifest'}
    if listed != expected:
        missing = sorted(set(expected) - set(listed))
        extra = sorted(set(listed) - set(expected))
        changed = sorted(k for k in listed.keys() & expected.keys()
                         if listed[k] != expected[k])
        raise ValueError(f'Content mismatch: missing={missing}, extra={extra}, changed={changed}')
    return {'archive': str(archive.resolve()), 'sha256': digest(archive),
            'bytes': archive.stat().st_size, 'members': len(listed),
            'manifest_files': len(manifest['files']), 'passed': True}


def package(output: Path, version: str, dry_run: bool) -> dict:
    """Publish only into a new output directory, then verify every member."""
    files = source_files(version)
    records = {str(path.relative_to(ROOT)): file_record(path) for path in files}
    package_count = sum(path.name == 'package.xml' and
                        path.relative_to(ROOT).parts[0] == 'src' for path in files)
    if package_count != 45:
        raise ValueError('Expected 45 ROS package manifests, found ' + str(package_count))
    summary = {'version': version, 'files': len(files), 'ros_packages': package_count,
               'source_bytes': sum(row.get('bytes', 0) for row in records.values()),
               'output': str(output), 'dry_run': dry_run}
    if dry_run:
        return summary
    output.mkdir(parents=True, exist_ok=False)
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', datetime.now(timezone.utc).timestamp()))
    prefix = 'peach_robot-v' + version
    manifest = {'schema': 'peach-source-release-v1', 'version': version,
                'archive_root': prefix,
                'created_utc': datetime.fromtimestamp(epoch, timezone.utc).isoformat(),
                'scope': ('Ubuntu 24.04 amd64 / ROS Jazzy / Python 3.12 / '
                          'CPU mock and frozen replay'),
                'runtime_baseline': '2026-11-07 02:44 Asia/Shanghai; see bundled evidence',
                'ros_packages': package_count, 'files': records}
    dump(output / 'RELEASE_MANIFEST.json', manifest)
    archive = output / (prefix + '.tar.zst')
    temporary = archive.with_suffix(archive.suffix + '.partial')
    process = subprocess.Popen(['zstd', '--quiet', '-T2', '-10', '-o', str(temporary)],
                               stdin=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdin, mode='w|', format=tarfile.PAX_FORMAT) as stream:
            sources = [*files, output / 'RELEASE_MANIFEST.json']
            for path in sources:
                rel = str(path.relative_to(ROOT)) if path in files else path.name
                row = records[rel] if path in files else file_record(path)
                info = tarfile.TarInfo(prefix + '/' + rel)
                info.mtime = epoch
                info.uid = info.gid = 0
                info.uname = info.gname = 'root'
                info.mode = int(row['mode'], 8)
                if row['type'] == 'symlink':
                    info.type = tarfile.SYMTYPE
                    info.linkname = row['target']
                    stream.addfile(info)
                elif row['type'] == 'directory':
                    info.type = tarfile.DIRTYPE
                    stream.addfile(info)
                else:
                    info.size = row['bytes']
                    with path.open('rb') as data:
                        stream.addfile(info, data)
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError('zstd compression failed')
    finally:
        if not process.stdin.closed:
            process.stdin.close()
        if process.poll() is None:
            process.terminate()
            process.wait()
    temporary.rename(archive)
    verified = check_archive(archive)
    sha_file = archive.with_name(archive.name + '.sha256')
    sha_file.write_text(verified['sha256'] + '  ' + archive.name + '\n')
    hashes = [row['sha256'] + '  ' + name for name, row in records.items()
              if row['type'] == 'file']
    (output / 'FILES.sha256').write_text('\n'.join(hashes) + '\n')
    notes = ROOT / 'docs/releases' / ('v' + version + '.md')
    shutil.copy2(notes, output / 'RELEASE_NOTES.md')
    dump(output / 'ARCHIVE_CHECK.json', verified)
    return {**summary, **verified}


def main() -> int:
    """Dispatch release preview, packaging or standalone archive checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--check', type=Path, metavar='ARCHIVE')
    args = parser.parse_args()
    if not shutil.which('zstd'):
        parser.error('zstd is required')
    try:
        if args.check:
            if args.output or args.dry_run:
                parser.error('--check cannot be combined with --output or --dry-run')
            result = check_archive(args.check)
        else:
            version = (ROOT / 'VERSION').read_text().strip()
            if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
                parser.error('VERSION must contain a stable numeric version such as 1.0.0')
            output = (args.output or ROOT.parent / 'releases' / ('v' + version)).resolve()
            result = package(output, version, args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, tarfile.TarError,
            EOFError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
