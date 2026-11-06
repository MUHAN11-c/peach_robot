#!/usr/bin/env python3
"""Verify a deployed Peach workspace, with explicit optional mock dry motion."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import errno
import importlib.metadata
import json
import math
import os
from pathlib import Path
import site
import socket
import subprocess
import sys
import time
import traceback
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src/peach/peach_system_tests/scripts'))
from peach_bringup.preflight import running_stack_pids  # noqa: E402
from run_live_camera_mock import defer_stop_signals, OwnedProcesses  # noqa: E402


def save(path: Path, value: object) -> None:
    """Atomically record observations, representing absent numeric states as null."""
    def normalize(item):
        """Convert nonfinite diagnostic values to strict JSON nulls."""
        if isinstance(item, float) and not math.isfinite(item):
            return None
        if isinstance(item, dict):
            return {key: normalize(entry) for key, entry in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalize(entry) for entry in item]
        return item
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(normalize(value), ensure_ascii=False,
                                    allow_nan=False, indent=2) + '\n')
    temporary.replace(path)


def inventory(path: Path) -> None:
    """Record process identities without dumping arguments or environments."""
    with path.open('w') as stream:
        subprocess.run(['ps', '-eo', 'pid,ppid,pgid,comm'], stdout=stream, check=True)


def check_environment(output: Path) -> dict:
    """Check locked packages, built assets and the effective runtime identity."""
    from packaging.requirements import Requirement
    import cv_bridge
    import numpy
    import open3d
    import torch
    import torchvision
    import ultralytics
    from ament_index_python.packages import get_package_share_directory
    requirements = []
    for line in (ROOT / 'requirements.txt').read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        requirement = Requirement(line)
        version = importlib.metadata.version(requirement.name)
        requirements.append({'package': requirement.name, 'version': version,
                             'matches': version in requirement.specifier})
    assert all(row['matches'] for row in requirements), requirements
    assert numpy.__version__ == '1.26.4'
    assert not site.ENABLE_USER_SITE
    assert sys.executable.startswith(str(ROOT / 'aubo_py3.12/'))
    assert cv_bridge.__file__.startswith('/opt/ros/jazzy/')
    planning_plugins = {name: get_package_share_directory(name) for name in (
        'pilz_industrial_motion_planner', 'moveit_planners_stomp')}
    cjk_fonts = subprocess.check_output(['fc-list', ':lang=zh', 'family'], text=True).splitlines()
    assert cjk_fonts, 'Missing CJK fonts for the Chinese console'
    for path in ('install/ros2_web_link/share/ros2_web_link/dist/sdk/index.js',
                 'install/peach_web/share/peach_web/web/vendor/peach-three.js'):
        assert (ROOT / path).is_file(), path
    identity = {
        'python': sys.executable, 'numpy': numpy.__version__,
        'torch': torch.__version__, 'torchvision': torchvision.__version__,
        'ultralytics': ultralytics.__version__, 'open3d': open3d.__version__,
        'cv_bridge': cv_bridge.__file__, 'usersite': site.ENABLE_USER_SITE,
        'requirements': requirements, 'hostname': socket.gethostname(),
        'namespaces': {key: os.readlink('/proc/self/ns/' + key)
                       for key in ('user', 'mnt', 'pid', 'ipc', 'net', 'uts')},
        'network_interfaces': [name for _, name in socket.if_nameindex()],
        'uid_map': Path('/proc/self/uid_map').read_text().strip(),
        'clean_room': os.environ.get('PEACH_CLEAN_ROOM') == '1',
        'planning_plugins': planning_plugins, 'cjk_font_families': cjk_fonts,
    }
    if identity['clean_room']:
        host_home = os.environ['PEACH_CLEAN_HOST_HOME']
        if host_home != '/root':
            assert not Path(host_home).exists()
        assert Path('/etc/peach-clean-room').is_file()
        assert not (ROOT / '.deps').exists()
        assert identity['network_interfaces'] == ['lo'], identity
    save(output / 'environment.json', identity)
    return identity


def check_ports() -> None:
    """Refuse to overwrite a running stack or occupied application port."""
    if running_stack_pids():
        raise RuntimeError('Existing ROS stack in this domain; refusing to start')
    for port in (8090, 9090):
        with socket.socket() as probe:
            probe.settimeout(1)
            result = probe.connect_ex(('127.0.0.1', port))
            if result == 0:
                raise RuntimeError('Application port already listening: ' + str(port))
            if result != errno.ECONNREFUSED:
                raise RuntimeError('Cannot inspect localhost port: ' + str((port, result)))


def readonly_mock(output: Path, web_e2e: bool) -> dict:
    """Start a frozen mock stack and inspect it without opening execution gates."""
    import rclpy
    from control_msgs.msg import DynamicJointState
    from controller_manager_msgs.srv import ListControllers, ListHardwareComponents
    from lifecycle_msgs.srv import GetState
    from moveit_msgs.srv import GetPlanningScene
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image, JointState, PointCloud2
    check_ports()
    output.mkdir()
    inventory(output / 'processes_before.txt')
    env = dict(os.environ, AUBO_RUNS_DIR=str(output / 'records'),
               ROS_LOG_DIR=str(output / 'ros_log'),
               NODE_PATH=str(ROOT / 'src/ros2_web_link/node_modules'))
    owner = OwnedProcesses(env, audit_path=output / 'owned_processes.json')
    completed = []
    node = None
    report = {'passed': False}
    try:
        stack = owner.start([
            'ros2', 'launch', 'peach_system_tests', 'frozen_camera_grasp.launch.py',
            'bag:=' + str(ROOT / 'runs/data/delivery_simulation_20261106/rgbd_frame_bag'),
            'frame_index:=0', 'hz:=2', 'rviz:=false'], log=output / 'stack.log')
        rclpy.init()
        node = rclpy.create_node('peach_deployment_probe')
        counts, received, subscriptions = Counter(), {}, []

        def callback(topic):
            """Build a finite stream observer for a selected topic."""
            def receive(message):
                """Keep counts and the latest state without modifying ROS resources."""
                counts[topic] += 1
                if topic == '/joint_states':
                    received[topic] = {
                        'name': list(message.name), 'position': list(message.position),
                        'velocity': list(message.velocity),
                        'effort': [value if math.isfinite(value) else None
                                   for value in message.effort]}
                elif topic == '/dynamic_joint_states':
                    received[topic] = {
                        name: dict(zip(values.interface_names, values.values))
                        for name, values in zip(message.joint_names, message.interface_values)}
                else:
                    received[topic] = {'width': message.width, 'height': message.height,
                                       'data_bytes': len(message.data)}
            return receive

        topics = [('/joint_states', JointState), ('/dynamic_joint_states', DynamicJointState),
                  ('/camera/color/image_raw', Image), ('/camera/depth/image_raw', Image),
                  ('/camera/depth_registered/points', PointCloud2)]
        for topic, kind in topics:
            subscriptions.append(node.create_subscription(
                kind, topic, callback(topic), qos_profile_sensor_data))
        deadline, next_http, state = time.monotonic() + 120, 0, None
        while time.monotonic() < deadline:
            if stack.poll() is not None:
                raise RuntimeError('Mock stack exited early')
            rclpy.spin_once(node, timeout_sec=.1)
            if time.monotonic() >= next_http:
                next_http = time.monotonic() + 1
                try:
                    with urllib.request.urlopen(
                            'http://127.0.0.1:8090/api/state', timeout=1) as response:
                        state = json.load(response)
                except (OSError, ValueError):
                    pass
            if ((state or {}).get('task_executor', {}).get('state')
                    and all(counts[topic] >= 3 for topic, _ in topics)):
                break
        else:
            raise RuntimeError('Mock readiness or RGB-D stream timeout')
        save(output / 'http_state.json', state)
        facts = state['startup']['facts']
        task = state['task_executor']['state']
        assert facts['hardware_mode'] == 'mock' and facts['autostart'] == 'false'
        assert str(facts['ros_domain_id']) == env['ROS_DOMAIN_ID']
        assert all(task.get(key) is False for key in (
            'execution_enabled', 'grasp_enabled', 'tool_enabled', 'action_active'))
        expected = ['shoulder_joint', 'upperArm_joint', 'foreArm_joint',
                    'wrist1_joint', 'wrist2_joint', 'wrist3_joint']
        joint, dynamic = received['/joint_states'], received['/dynamic_joint_states']
        assert joint['name'] == expected
        assert len(joint['position']) == len(joint['velocity']) == 6
        assert len(joint['effort']) in (0, 6)
        initial = [.425175, .194274, 1.679546, 1.462579, -.279948, .038859]
        for index, name in enumerate(expected):
            assert abs(joint['position'][index] - initial[index]) < 1e-6
            assert abs(joint['velocity'][index]) < 1e-6
            for field in ('position', 'velocity', 'effort'):
                if field in dynamic[name]:
                    assert len(joint[field]) == 6
                    assert abs(joint[field][index] - dynamic[name][field]) < 1e-6
                elif field == 'effort':
                    assert not joint[field] or joint[field][index] is None
        assert 'speed_scaling' in dynamic and 'aubo_io' in dynamic
        publishers = {topic: [item.node_name for item in node.get_publishers_info_by_topic(topic)]
                      for topic in ('/joint_states', '/dynamic_joint_states')}
        assert publishers == {'/joint_states': ['joint_state_broadcaster'],
                              '/dynamic_joint_states': ['dynamic_joint_state_broadcaster']}

        def query(kind, name):
            """Query one read-only ROS service with a bounded wait."""
            client = node.create_client(kind, name)
            try:
                assert client.wait_for_service(timeout_sec=10), name
                future = client.call_async(kind.Request())
                rclpy.spin_until_future_complete(node, future, timeout_sec=10)
                result = future.result()
                assert result is not None, name
                return result
            finally:
                node.destroy_client(client)

        hardware = query(ListHardwareComponents, '/controller_manager/list_hardware_components')
        plugins = {component.name: component.plugin_name for component in hardware.component}
        assert plugins.get('AuboE5System') == 'mock_components/GenericSystem'
        response = query(ListControllers, '/controller_manager/list_controllers')
        controllers = {controller.name: controller.state for controller in response.controller}
        assert all(controllers.get(name) == 'active' for name in (
            'joint_state_broadcaster', 'dynamic_joint_state_broadcaster',
            'joint_trajectory_controller'))
        lifecycle = {}
        for name in ('peach_scene_perception_node', 'peach_target_reconstruction_node',
                     'peach_arm', 'peach_supervisor'):
            for _ in range(15):
                label = query(GetState, '/' + name + '/get_state').current_state.label
                if label == 'active':
                    break
                rclpy.spin_once(node, timeout_sec=.5)
            lifecycle[name] = label
        assert all(label == 'active' for label in lifecycle.values()), lifecycle
        query(GetPlanningScene, '/get_planning_scene')
        pages = {}
        for page in ('/', '/overview.html', '/monitor.html', '/debug.html',
                     '/analysis.html', '/force.html'):
            with urllib.request.urlopen('http://127.0.0.1:8090' + page, timeout=5) as response:
                pages[page] = response.status
                assert response.status == 200
        websocket = owner.start([
            'node', str(ROOT / 'scripts/deployment/probe_websocket.js'),
            str(output / 'websocket.json')], log=output / 'websocket.log')
        assert websocket.wait(timeout=25) == 0, 'WebSocket projection failed'
        completed.append(websocket)
        if web_e2e:
            browser = subprocess.check_output([
                'node', '-e', 'console.log(require("playwright").chromium.executablePath())'],
                env=env, text=True).strip()
            web = owner.start([
                'node', str(ROOT / 'src/peach/peach_web/scripts/e2e-console.js'),
                '--browser', browser, '--transport', 'http', '--out', str(output / 'web_e2e')],
                log=output / 'web_e2e.log')
            assert web.wait(timeout=300) == 0, 'Web browser E2E failed'
            completed.append(web)
        report.update(passed=True, controllers=controllers, lifecycle=lifecycle, plugins=plugins,
                      planning_scene_service_ready=True,
                      counts=dict(counts), received=received, publishers=publishers, pages=pages,
                      enables={key: task[key] for key in (
                          'execution_enabled', 'grasp_enabled', 'tool_enabled', 'action_active')})
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            if node is not None:
                node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
        except Exception as error:
            report['probe_cleanup_error'] = repr(error)
            report['passed'] = False
        with defer_stop_signals():
            report['residuals'] = owner.cleanup(completed=completed)
        report['cleanup_issues'] = owner.cleanup_issues
        if report['residuals'] or report['cleanup_issues']:
            report['passed'] = False
        inventory(output / 'processes_after.txt')
        save(output / 'report.json', report)
    assert report['passed'], report
    return report


def frozen_grasp(output: Path) -> dict:
    """Run the existing mock-only driver and check its own new ledger."""
    check_ports()
    output.mkdir()
    inventory(output / 'processes_before.txt')
    request = 'deploy_' + uuid.uuid4().hex[:12]
    env = dict(os.environ, AUBO_RUNS_DIR=str(output / 'records'),
               ROS_LOG_DIR=str(output / 'ros_log'))
    owner = OwnedProcesses(env, audit_path=output / 'owned_processes.json')
    completed = []
    report = {'passed': False, 'request': request, 'tool_enabled': False}
    try:
        driver = owner.start([
            'ros2', 'run', 'peach_system_tests', 'run_frozen_grasp.py',
            '--bag', str(ROOT / 'runs/data/delivery_simulation_20261106/rgbd_frame_bag'),
            '--index', '0', '--hz', '2', '--ready-timeout', '120', '--timeout', '180',
            '--request-id', request], log=output / 'run.log')
        result = driver.wait(timeout=480)
        completed.append(driver)
        assert result == 0, 'Frozen driver failed'
        ledger = json.loads((output / 'records' / request / 'ledger.json').read_text())
        successful = [row for row in ledger['outcomes']
                      if row['outcome'] == 0 and row.get('completion_level', 0) >= 6]
        assert successful, ledger
        text = (output / 'run.log').read_text()
        assert 'replay_paused=True' in text
        assert 'owned process groups clean' in text
        assert 'tool.enabled=false' in text
        report.update(passed=True, wrapper_exit=result, ledger=ledger, replay_paused=True,
                      single_target_successes=len(successful),
                      interpretation='Single fruit L6; fixture cancels the batch; tool disabled.')
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        with defer_stop_signals():
            report['residuals'] = owner.cleanup(completed=completed)
        report['cleanup_issues'] = owner.cleanup_issues
        if report['residuals'] or report['cleanup_issues']:
            report['passed'] = False
        inventory(output / 'processes_after.txt')
        save(output / 'report.json', report)
    assert report['passed'], report
    return report


def check_recordings(output: Path) -> list[dict]:
    """Stream every finalized session bag and compare the recorded message count."""
    import rosbag2_py
    import yaml
    reports = []
    for metadata in output.glob('*/records/session_*/bag/metadata.yaml'):
        bag = metadata.parent
        expected = yaml.safe_load(metadata.read_text())['rosbag2_bagfile_information']
        reader = rosbag2_py.SequentialReader()
        reader.open(
            rosbag2_py.StorageOptions(uri=str(bag), storage_id=expected['storage_identifier']),
            rosbag2_py.ConverterOptions('cdr', 'cdr'))
        count = 0
        while reader.has_next():
            reader.read_next()
            count += 1
        assert count == expected['message_count'], (bag, count, expected['message_count'])
        reports.append({'bag': str(bag), 'messages': count, 'passed': True})
    assert reports, 'No session recordings generated'
    save(output / 'recordings.json', reports)
    return reports


def main() -> int:
    """Verify one deployment and preserve its result even on failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--grasp', action='store_true')
    parser.add_argument('--web-e2e', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault('ROS_DOMAIN_ID', '181')
    os.environ['ROS_LOCALHOST_ONLY'] = '1'
    report = {'passed': False, 'started_utc': datetime.now(timezone.utc).isoformat()}
    inventory(output / 'processes_before.txt')
    try:
        report['environment'] = check_environment(output)
        report['readonly_mock'] = readonly_mock(output / 'readonly_mock', args.web_e2e)
        if args.grasp:
            report['frozen_grasp'] = frozen_grasp(output / 'frozen_grasp')
        report['recordings'] = check_recordings(output)
        check_ports()
        report['passed'] = True
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        inventory(output / 'processes_after.txt')
        report['finished_utc'] = datetime.now(timezone.utc).isoformat()
        save(output / 'verification.json', report)
        displayed = {key: report[key] for key in report if key in (
            'passed', 'started_utc', 'finished_utc', 'error', 'traceback')}
        print(json.dumps(displayed, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
