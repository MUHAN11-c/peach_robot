# ivg_bringup

IVG 独立演示栈的机械臂基础组合。公共入口为 `launch/ivg_system.launch.py`，默认 `hardware_mode=mock`、`gripper=none`；`robot_ip` 仅供 real 模式硬件插件使用。

launch 通过 `ivg_moveit_config.build_moveit_config` 生成同一工具的 URDF/SRDF，启动 robot_state_publisher、ros2_control_node、joint_state_broadcaster、选定轨迹控制器与 move_group。mock 使用 joint_trajectory_controller，real 使用 aubo_passthrough_trajectory_controller 并额外加载 aubo_io_controller。硬件插件与控制器配置复用只读 AUBO 包。

本入口不启动相机、手眼 TF、视觉算法、演示业务服务或 Web，不主动发送运动/IO，也不启动 dashboard。启动 real 栈不构成运动/SetIO 授权；工作区禁止启动或调用 dashboard，硬件急停不经 ROS。

部署工具集合与模型来源见 [ivg_description](../ivg_description/README.md)，规划配置见 [ivg_moveit_config](../ivg_moveit_config/README.md)。IVG 与 Peach 主链独立，手工运行时须自行选择隔离的 ROS_DOMAIN_ID；launch 不设置域。

以上为 2026-11-06 源码核对，未启动或验证运行链。
