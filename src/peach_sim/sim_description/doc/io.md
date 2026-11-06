# sim_description 模型接口

资源包，没有节点或 console script。CMake 安装 urdf/meshes/config/doc；模型由 sim_bringup 展开并交给 RSP、MoveIt 和 Gazebo。当前 Gazebo 暂停，以下为源码契约。

## Xacro 输入和装配

当前入口 urdf/harvester_unified.urdf.xacro 的 tool_profile 支持 shear_v1、bite_shear_v1、adaptive_shear_v1，底层默认 bite_shear_v1，未知档案拒绝。平台尺寸、arm_mount_height、arm_mount_yaw_deg 由 sim_worlds.params.xacro_mappings 从 orchard.yaml 显式注入；wrist_camera 默认 true。联合 harvest 默认选 adaptive 档，独立 sim.launch 默认 bite 档，不能与 xacro 缺省混为同一层配置。

URDF robot.name 为 aubo_e5，以匹配只读 SRDF；Gazebo 实体名为 harvester；根 link 为 platform_base_link，base_link 经 arm_mount_joint 固定到平台。六活动关节依次为 shoulder_joint、upperArm_joint、foreArm_joint、wrist1_joint、wrist2_joint、wrist3_joint。aubo_e5_arm.xacro 是去掉 world/world_joint 的臂链快照，网格仍引用 aubo_description，来源限位/惯量不能由本包另立标准。

tracked_platform.xacro 是共享宏，仍保留历史 mobile/锚定分支；当前统一机体固定传 mobile=true、chassis_visual=bunker，保留 YAML 中安装偏航，不适用头注释中旧导航“偏航归零”的描述。harvester_robot.urdf.xacro 是旧两模式源文件，当前 launch 不选它；不能把其 JointPositionController/JointStatePublisher 当作现行控制链。

## 输出和所有权

RSP 发布 platform→arm/tool 与 wrist3→camera_link→color/depth→optical 固定/运动 TF。RGB-D 图像使用 optical_frame_id，原生点云为 camera_link 的 +X forward；sim_bridge 显式保留这个区别，不能统一把所有点云 XYZ 当作光学坐标。当前模型提供 camera_color_optical_frame 与 camera_depth_optical_frame 两个同几何光学帧。

底盘 VelocityControl 消费 Gazebo /cmd_vel；OdometryPublisher 产生 /odom 和 odom→platform_base_link，map→odom 不由本包发布。激光源 /scan、10Hz、lidar_mount；RGB-D 源 camera/depth、640×480、2.5Hz、0.2–1.0m clip，话题通过组合包桥到 /camera/*。

臂由 GazeboSimSystem 的 position command、position/velocity state 接口连接现行 JSB/JTC；joint_states 原生 ROS 发布，不经旧 Gazebo 关节桥。控制器配置保持只读。sim_worlds.add_harvest_plugins 在生成副本中注入 SRDF harvest_stow 初值及每目标 DetachableJoint；筐接触传感器与工具/果实碰撞 mask 在生成 SDF 阶段适配，均不回写本包源模型。

harvest_basket 是固定平台 link；Gazebo 中的已采袋果释放后仍为自由刚体，MoveIt 的筐负载附着只服务规划。来源、物理代理与历史离线核对边界见 [architecture.md](architecture.md)。
