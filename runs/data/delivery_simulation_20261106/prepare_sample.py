#!/usr/bin/env python3
"""Extract a synchronized, unmodified RGB-D fixture from the recorded source."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import rosbag2_py
from rclpy.serialization import serialize_message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    sys.path.insert(0, str(workspace / 'src/peach/peach_system_tests/scripts'))
    from frozen_camera_replay import load_frame, _stamp_ns

    source = workspace / (
        'runs/data/ros2_web_live_camera_mock_20261028/'
        'capture_before_camera_off/peach_rgbd_mock_60s')
    index = 2
    frame = load_frame(str(source), index)
    output = args.output.resolve()
    bag = output / 'rgbd_frame_bag'
    if bag.exists():
        raise FileExistsError(f'Refusing to overwrite {bag}')
    output.mkdir(parents=True, exist_ok=True)
    writer = rosbag2_py.SequentialWriter()
    writer.open(
        rosbag2_py.StorageOptions(uri=str(bag), storage_id='mcap'),
        rosbag2_py.ConverterOptions('cdr', 'cdr'))
    for topic_id, (name, message) in enumerate(frame.items(), start=1):
        ros_type = ('sensor_msgs/msg/CameraInfo' if name.endswith('camera_info')
                    else 'sensor_msgs/msg/PointCloud2' if name.endswith('points')
                    else 'sensor_msgs/msg/Image')
        writer.create_topic(rosbag2_py.TopicMetadata(
            id=topic_id, name=name, type=ros_type, serialization_format='cdr'))
        writer.write(name, serialize_message(message), _stamp_ns(message))
    del writer
    inputs = output / 'perception_inputs'
    inputs.mkdir(exist_ok=True)
    for path in sorted((workspace / 'runs/data/peach_fps_audit_20261026/inputs').glob('*.npz')):
        shutil.copy2(path, inputs / path.name)
    provenance = {
        'source_bag': str(source.relative_to(workspace)),
        'source_rgb_index': index,
        'selection': 'Original RGB/depth/cloud exposure stamps exactly equal; no retiming.',
        'sensor_stamp_ns': {name: _stamp_ns(msg) for name, msg in frame.items()},
        'perception_inputs_source': 'runs/data/peach_fps_audit_20261026/inputs',
        'purpose': 'Frozen-camera mock replay and offline perception; no hardware required.',
        'files': {},
    }
    for path in sorted(output.rglob('*')):
        if path.is_file() and path.name != 'provenance.json':
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(chunk)
            provenance['files'][str(path.relative_to(output))] = {
                'bytes': path.stat().st_size, 'sha256': h.hexdigest()}
    (output / 'provenance.json').write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(provenance, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
