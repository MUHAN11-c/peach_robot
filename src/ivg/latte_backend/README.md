# latte_backend

IVG 咖啡拉花编排，2026-09-30 从 aubo_boot 移植。运动复用 ivg_demo_services::RobotController，IO 经 aubo_io_controller；独立于 Peach lifecycle。

## 公共入口与实际流程

`launch/latte_workflow.launch.py` 参数为 gripper（默认 none）、hardware_mode（默认 mock）、robot_ip，加载同工具的 IVG MoveIt 配置并启动两个节点。IO 旁路由 hardware_mode 推导，没有 io_simulated launch 参数。launch 不主动调用工作流，也不启动 move_group/控制器。

- `latte_workflow_node` 提供 `/latte/run_workflow`（RunLatteWorkflow，空请求），串行处理请求并在每次开始重新读取 lwf_* 参数。实际调用 step1 取奶 → step2 打泡 → step3 转腕/放置 → step5 心形轨迹；step0 取放咖啡杯与 step4 前倾保留但未调用。
- `lwf_execute_latte` 在 launch 中为 true。设为 false 只跳过 step5 轨迹执行，前三步仍会运动，不能作为全流程预览开关。
- `liblatte_trajectory.a` 的 LatteTrajectoryGenerator 生成 Approach、Mix、Draw、Finish、Home 五段：靠近、融合画圈、成形注入、划穿、恢复水平。spoutToTcp 用姿态旋转 TCP 局部喷嘴偏移后从喷嘴位置扣除，输出 TCP 路点；各段倾角按参数绝对起算，不依赖未执行的 step4。
- `latte_io_node` 提供 `/set_latte_do2`、`/set_latte_do4`（SetBool → SetIO，默认 DO2/DO4）；收到 IOState 时把 digital_in 发布为 `/latte_di_status` JSON，没有定时心跳。
- `spout_calibrator.py` 每 0.05 秒发布 tool_tcp → spout_marker 的 TF 和 `/spout_marker` Marker，可实时调 ox/oy/oz。它不自动把结果写回工作流，确认后须同步 lwf_spout_offset_*。

预教关节角、杯口/喷嘴偏移及 MSLA 轨迹参数见源码声明；这些默认值不是本轮实物标定或拉花效果的验证结论。

## 运行边界与检查

io_simulated 只旁路 IO，运动仍交给 MoveIt。真机运动/SetIO 须操作员明确授权；启动 real 栈不构成授权。工作区禁止启动/调用 dashboard，硬件急停不经 ROS。

```bash
colcon build --packages-up-to latte_backend
colcon test --packages-select latte_backend
colcon test-result --verbose
```

CMake 当前只注册 ament lint，无轨迹行为测试目标。2026-11-06 仅静态核对，未执行拉花/标定/IO。许可 BSD-3-Clause。
