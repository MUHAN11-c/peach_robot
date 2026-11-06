# ivg_demo_services

IVG 演示运动与服务适配，2026-09-30 从 aubo_boot 按需移植。独立于 Peach harvest_system/lifecycle，运动使用 MoveIt，IO 使用 `/aubo_io_controller/set_io`。

## 公共入口与实际行为

`launch/demo_services.launch.py` 声明 gripper（默认 none）、hardware_mode（默认 mock）、robot_ip，自动加载 `config/demo_services.yaml` 和同工具的 IVG MoveIt 参数。它不启动 move_group、控制器、相机或 TF。launch 按 hardware_mode 覆盖 io_simulated；不存在同名 launch 参数。末端为 tool_tcp，选 gripper2 时抓取节点改用 grasp_tcp。

- `move_service_node`：`/move_to_pose`、`/debug/move_to_xyz`（MoveToPose）、`/get_current_state`、`/read_robot_io`、`/set_robot_enable`、`/set_speed_factor`。运动回调共享互斥组，查询回调另组。use_joints 选择关节目标或 TCP 笛卡尔直线；非正倍率取节点当前默认，正倍率上限为 1。SetSpeedFactor 仅更新后续请求的默认速度，非正值保留当前值，不修改硬件限速。
- `grasp_trigger_node`：订 `/grasp_poses_base`，提供 `/execute_single_grasp`（ExecuteGraspPose）、`/loop_grasp_control` 和 `/publish_grasps_worker_loop_control`（SetBool）。循环默认关闭；busy 标志使周期串行。周期为回 home → 读缓存视觉位姿或预设位姿 → 开爪 → 分段接近 → 闭爪 → 抬升 → 放置偏移 → 开爪，末尾没有额外回 home。视觉选择按 `abs(Rzz)` 取双向竖直程度最高者，不按 object_id 筛选，也不检查 PoseArray 的 stamp/新鲜度。停止循环只阻止后续周期，不取消正在执行的周期。
- `system_monitor_node`：订 `/aubo_io_controller/robot_status`，每秒发布一个逻辑名 aubo_driver 的 NodeStatus（transient_local）；不是全图节点存活检查。收到过状态后超过 5 秒为 offline，急停/错误为 error，未上电为 degraded。last_heartbeat 是监控发布时刻，uptime 是监控自身运行时长。SystemLog 当前只发布启动事件，不聚合全栈日志。
- `libdemo_motion`：RobotController 提供同步 MoveIt 规划/执行与 DO 封装；motion_utils 提供插值和路点构造。

`io_simulated=true` 仅旁路 IO，运动仍提交给 MoveIt。此包没有 Peach 的 lifecycle、clearance 或使能门。

## 兼容服务与运行边界

`/set_robot_enable` 源码仍转发 dashboard 的 `/aubo/startup`、`/aubo/stop`；它不是急停。工作区禁止启动/调用 dashboard，不能把这一兼容入口当作可用操作指引。FK 在 RobotController 使用本地 RobotState；外部旧 dashboard FK/IK 客户端不属于本包运动必需链。

真机运动和 SetIO 须操作员明确授权；启动 real 栈本身不构成授权。硬件急停通过柜/示教器，不经 ROS。IVG 与 Peach 不同机同域运行，launch 不设置 ROS_DOMAIN_ID。

## 构建与静态检查

```bash
colcon build --packages-up-to ivg_demo_services
colcon test --packages-select ivg_demo_services
colcon test-result --verbose
```

CMake 当前仅注册 ament lint，没有 gtest 行为用例。scripts 中 aubo_mode.py、limit_workspace.py（配 workspace_limits.yaml）、publish_gripper_joint_states.py、publish_obstacle.py 是手工工具，会发布模式/状态/场景，不是自动测试。

2026-11-06 仅依据源码修订说明，未启动、调用或重新验证演示链。许可 Apache-2.0。
