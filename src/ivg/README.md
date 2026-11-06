# IVG 独立演示栈源码导航

按 2026-11-06 当前 package.xml、launch 和包入口整理。IVG 与 `src/peach/` 采摘主链独立，使用 `ivg_interfaces`；不加入 Peach 的 lifecycle 或接口清单。各包 README 记录各自行为，历史试验结果须保留日期和配置。

| 包 | 当前职责与入口 |
|---|---|
| [ivg_bringup](ivg_bringup/README.md) | `launch/ivg_system.launch.py` 组合单一部署工具 URDF、ros2_control、状态发布与 MoveIt；默认 mock/gripper=none，无自动运动或 IO |
| [ivg_description](ivg_description/README.md) | 工具/夹爪描述与 `description.py` 的部署工具集合 |
| [ivg_moveit_config](ivg_moveit_config/README.md) | `configuration.py::build_moveit_config` 为同一工具模型生成 MoveIt 配置 |
| [ivg_interfaces](ivg_interfaces/README.md) | 模板估姿、演示服务及消息 IDL |
| [ivg_pose_estimation](ivg_pose_estimation/README.md) | 独立模板 6D 估姿、分割/匹配流水线及旁路 Web |
| [ivg_graspnet](ivg_graspnet/README.md) | 点云抓取检测与独立 MoveIt 接近，双后端 |
| [ivg_demo_services](ivg_demo_services/README.md) | 演示运动薄层与服务适配 |
| [tool_changer](tool_changer/README.md) | 数据驱动快换与附着场景同步 |
| [latte_backend](latte_backend/README.md) | 拉花工作流、轨迹纯核、标定及 IO 桥 |
| [aubo_ros2_web_dashboard](aubo_ros2_web_dashboard/README.md) | 8095 FastAPI 网关与演示面板；旧共享 JS/ros_web_link 依赖缺失，见包 README |
| [ivg_foxglove_bridge](ivg_foxglove_bridge/README.md) | 上述 Web 的 Foxglove/CDR 服务端，默认监听 0.0.0.0:8765；与 Peach 的 ros2_web_link/ROSbridge 路径区分 |
| [ivg_sim](ivg_sim/README.md) | 独立 Gazebo 桌面抓取与评分环境，当前遵循全工作区 Gazebo 暂停约束 |

`ivg_bringup` 直接复用只读 AUBO 硬件插件和控制器配置；real 模式额外加载 IO 控制器。源码中独立运动/工具入口不构成运行授权。当前工作区约束见 [AGENTS.md](../../AGENTS.md)：禁止启动/调用 dashboard，真机运动或 SetIO 须操作员授权，保持默认使能/自动运行关闭。

第三方 Foxglove、websocketpp、抓取算法库及模型来源按各包 provenance/许可维护；不能因不属于 Peach 主链就归档依赖。模型获取见 [ivg_pose_estimation/models](ivg_pose_estimation/models/README.md)。本次只核对静态源码和文档，未启动演示栈、硬件或仿真。
