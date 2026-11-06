# 2026-11-06 可直接复现的无硬件数据

本目录提供实际验证过的冻结 RGB-D 回放包和离线感知输入，不依赖相机、串口或 Gazebo。

## 数据与来源

- `rgbd_frame_bag/`：一组原始同步帧，含 RGB、深度、两路 CameraInfo 和已配准点云，传感器曝光时间差为 0。RGB/深度 640×480，点云 171892 点。
- 来源为 `runs/data/ros2_web_live_camera_mock_20261028/capture_before_camera_off/peach_rgbd_mock_60s` 的 RGB 索引 2；未改图像、深度、点云和原始时间戳。精简包不含完整原始 bag，来源路径只用于追溯。
- `perception_inputs/`：复制自 `runs/data/peach_fps_audit_20261026/inputs` 的 8 个真实 RGB-D `.npz`，包含 `rgb_bgr`、`depth_raw`、`K` 和原数据提供的 `T`。
- `provenance.json`：来源、时间戳、文件字节数与 SHA-256；`prepare_sample.py` 仅供另行持有原始 bag 时重新提取，不覆盖已有 bag；运行随包样例不需要该原始录包。
- `verified_ledger.json`：本轮已验证的单果 L6 干跑账本。完整会话录包和旧试验产物不进入精简包；运行日志与验收摘要在本轮 analysis_reports 目录。

`rgbd_frame_bag` 是单帧冻结夹具，不是时间序列。它通过现有冻结发布器重发实时戳，用于单视夹具；多视覆盖、真实剪切和全部目标成功率不由它证明。

## 环境

先按`docs/deployment-20261106.md` 完成恢复构建与环境加载。以下命令从工作区根执行。
确认 ROS 域 181、HTTP 8090 和 WS 9090 空闲；不要覆盖其他任务的实例。

## 只读回放与网页

```bash
export ROS_DOMAIN_ID=181 ROS_LOCALHOST_ONLY=1
export AUBO_RUNS_DIR="$PWD/runs/data/my_replay"
ros2 launch peach_system_tests frozen_camera_grasp.launch.py \
  bag:="$PWD/runs/data/delivery_simulation_20261106/rgbd_frame_bag" \
  frame_index:=0 hz:=2 rviz:=false
```

launch 不发抓取请求，执行/接触/工具使能及 autostart 保持关闭。浏览器打开 `http://127.0.0.1:8090`。
退出用 Ctrl+C，等待 bag 封口及本轮进程退出。不要直接 `ros2 bag play --loop` 这个零时长单帧包。

## 单果完整干跑

先退出上面的只读回放。以下是显式 mock 测试驱动，会打开 mock 执行/接触并运行运动，始终 `tool=false`：

```bash
export ROS_DOMAIN_ID=181 ROS_LOCALHOST_ONLY=1
export AUBO_RUNS_DIR="$PWD/runs/data/my_frozen_grasp"
ros2 run peach_system_tests run_frozen_grasp.py \
  --bag "$PWD/runs/data/delivery_simulation_20261106/rgbd_frame_bag" \
  --index 0 --hz 2 --ready-timeout 120 --timeout 180
```

本轮 wrapper 退出 0，单果 target_1 达到 L6，回放暂停且自有进程组无残留。
另一个目标因 `bag_axis_envelope_ill_conditioned` 被拒绝。wrapper 在第一颗成功后取消批次，
因此 Action `CANCELED`、批次 `success=false` 与单果 L6 同时存在；不是 PICK_ALL 全目标自然成功，也不证明真实剪切。

## 离线感知

```bash
python3 src/peach/peach_system_tests/scripts/benchmark_perception.py \
  --input-dir runs/data/delivery_simulation_20261106/perception_inputs \
  --max-frames 3 --warmup 1 --json-out /tmp/peach_delivery_benchmark.json
```

本轮实际执行 3 帧，1 帧预热、2 帧稳态；稳态每帧 5 个检测、4 个候选。性能数字只代表该次环境与短样本。
日志和完整运行验证位于 `runs/analysis_reports/delivery_20261106/`。
