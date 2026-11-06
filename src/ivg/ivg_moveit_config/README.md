# ivg_moveit_config

`ivg_moveit_config.configuration.build_moveit_config` 为 IVG 同一部署工具组合 URDF、SRDF 与 MoveIt 参数。默认 `gripper=none`、`hardware_mode=mock`，也可传入显式 robot_description / robot_description_semantic。

工具集合来自 ivg_description；SRDF 由本包 xacro 生成。运动学、关节限位和 Pilz 笛卡尔限位复用只读 aubo_e5_moveit_config。mock/real 分别选择其 controllers_mock.yaml / controllers.yaml；MoveIt 不管理控制器切换。配置开放 ompl、pilz_industrial_motion_planner、stomp，默认管线为 Pilz。

公共 Python 构建器供 [ivg_bringup](../ivg_bringup/README.md)、演示服务、快换、拉花及仿真组合使用。它只构造配置，不启动节点或发送运动。固定工具模型必须在各消费者中保持一致；快换入口要求 `gripper=none`。

CMake 安装 config、launch、.setup_assistant 及 Python 模块。这里只核对配置来源，未改动或运行控制器、规划器。
