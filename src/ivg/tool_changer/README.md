# tool_changer

IVG 数据驱动工具快换，2026-09-30 从 aubo_boot 移植。运动复用 ivg_demo_services::RobotController，DO 经 `/aubo_io_controller/set_io`；不进入 Peach lifecycle。

## 配置与模型

两节点均读取 `ivg_description/config/tools.yaml`，mesh 位于 ivg_description/meshes。五个工具档案为 gripper0/1/2、gripper1coffeecup、gripper1milkcup；杯具没有物理 dock 轨迹。取放采用 vertical 或 slide 策略，实际方向、深度、停留时间来自配置。

`launch/gripper_swap_worker.launch.py` 参数为 gripper（默认 none）、hardware_mode（默认 mock）、robot_ip、initial_tool_id（默认空）。物理快换要求 gripper=none；非 none 的固定工具部署会被 launch 拒绝。launch 自动按 mock/real 设置 IO 旁路，不声明 attach_frame、io_simulated 或 tool_profile 参数。

## 公共入口与流程

- 可执行 `gripper_swap_worker_node`（节点 gripper_swap_worker）：`/change_tool`（ChangeTool）、`/run_gripper_swap`（RunGripperSwap）、`/get_current_tool`（GetCurrentTool）。流程为释放当前工具 → 取目标 → 更新软件状态 → 回 home；中途失败不是事务性回滚。节点退出清理仍会尝试回 home，运行/停止都须纳入操作安排。
- `/tool_changer_status`：启动、流程变化时及每 5 秒发布，来自 current_tool_ 软件状态；没有 DI 轮询或锁紧限位确认。initial_tool_id 和 direction 中的源工具可补充软件状态，不能证明实物安装情况。
- 可执行 `scene_attach_worker_node`：服务 `/scene_attach`、`/scene_detach`、`/set_display_tool`（均 ChangeTool）。按工具状态更新 `/attached_collision_object` 和 `/planning_scene` diff，默认附着帧 kuaihuan_Link。固定 modeled_tool 时忽略动态工具状态。
- `/set_display_tool` 只检查请求与当前部署/附着工具是否一致，不更换实物、不修改 URDF/SRDF、不发布 robot_description，也不改变 RSP 的 TF 树。本包 urdf/ 静态文件虽仍被安装，当前附着处理器不读取它们。

节点参数 io_simulated / simulation_skip_io 或 `/aubo/mode` 的 simulation 模式只旁路 IO，不旁路运动；launch 仍组合 MoveIt 参数，需要外部 move_group 和控制器。真机运动/SetIO 须操作员明确授权，启动 real 栈不构成授权。

## 手工工具与检查

scripts/test_tool_change.py 会调用换工具服务；attach_test.py 会直接改 PlanningScene；scene_monitor.py 观察场景。它们不是自动行为测试。compute_dock_ik.py 保留旧 dashboard `/aubo/get_ik` 客户端，当前工作区禁止启动/调用 dashboard，不作为可运行标定指引。

```bash
colcon build --packages-up-to tool_changer
colcon test --packages-select tool_changer
colcon test-result --verbose
```

CMake 当前仅注册 ament lint，没有 gtest 行为目标。2026-11-06 仅核对源码，未启动或调用快换链。许可 BSD-3-Clause。
