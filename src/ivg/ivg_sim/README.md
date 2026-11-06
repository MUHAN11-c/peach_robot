# ivg_sim

IVG 独立 Gazebo Harmonic 桌面抓取与评分环境，通过参数组合 ivg_graspnet，不进入 Peach harvest_system/lifecycle。工作区目前暂停 Gazebo；以下描述供源码理解，恢复仿真须另行明确授权，本轮没有启动或重新验证。

## 当前公共入口（2026-11-06 源码）

- `ivg_table_sim.launch.py`：零重力检测评分场景，固定 RGBD 相机、点云桥、中继、静态 TF 和检测节点。layout.py 从 config/table_layout.yaml 生成相机/桌面/对象布局；当前场景放置 10 个对象，模型库有 16 个。cloud_relay 只重写 PointCloud2 的 header.frame_id，不旋转点坐标，点云轴约定必须与该链一致。
- `ivg_grasp_sim.launch.py`：每次生成重力 9.81 的执行世界，不放固定相机架，使用腕上相机 camera_color_optical_frame。默认且仅接受 gripper2，当前四指模型使用原始 CAD 子装配与四个 gripper2_*_joint，不是历史 Allegro 手。启动 Gazebo、RSP、控制器、move_group、点云链和检测节点，不自动运行 execute_grasp。机械臂 world → base_link 的摆放与 spawn 共用 arm_description.SPAWN_XYZ；MoveIt 参数通过 ivg_moveit_config 构建器组合。
- `gripper_contact.launch.py` / `gripper_contact_test`：独立夹爪接触试验。后者会自行启动 launch、发布四指 effort 和夹具升降命令，读取 Gazebo 实物位移，并在 finally 清理其进程组；不是静态或硬件无关的 lint。

上述 launch 不设置 ROS_DOMAIN_ID。gripper_contact_test 自行设置域 97 和独立 Gazebo partition；其余运行链需由操作者隔离域。控制器配置、硬件/ros2_control 描述在本轮保持只读。

## 世界生成、评分与执行的区别

`generate_table_world` 根据 YAML 生成 SDF 和同名 manifest（摆位/相机/seed/sha256），默认零重力，有重力时默认文件名增加 _grasp。可选 jitter 必须提供 seed。执行 launch 会重新生成自己的默认布局，不能把此前单独生成的 jitter 文件当作该入口必然采用的输入。模型网格恢复方式见 [models/README.md](models/README.md)。

`score_grasps` 调 `/graspnet_capture_control`，等待 PoseArray 后按 manifest 评分：XY 命中半径 radius+0.02 m，Z 范围桌面-0.02 到桌面+2r+0.05 m。输出覆盖率、最近 XY 距离、双向竖直度；coverage ≥0.4 决定退出码。它是检测几何评分，不验证抓取接触或夹持。manifest 优先查 ament share/worlds，其次 IVG_SIM_WORLDS；最后硬编码的 src/ivg_sim/worlds 是旧目录回退，当前源码树不能依赖它。

`execute_grasp` 使用 JTC 回拍照位、触发检测、选择目标附近的检测 XY/yaw，随后以 Gazebo 真值对象位置/碰撞中心替换位置并约束竖直姿态。之后注入场景、effort 开爪、两段高位 JTC 转移、IK/FK 与 Gazebo XY 残差修正、密集 IK 下降、两段 effort 闭合、抬升，再读对象位移判定。这是带真值辅助的接触执行链，不能作为纯感知端到端精度证据。

位移判定优先 Δz>0.05 m 为成功，随后 Δxy>0.08 m 为失败；较小位移可记 partial。程序正常走到末尾仍返回 0，须读取 JSON verdict，不能用退出码 0 判定夹持成功。默认核验后开爪，--keep 可保持闭合。等待 capture 服务的 while 当前没有总超时，后面的位姿等待超时不覆盖这一段。

## 历史记录与检查范围

2026-09-29 RTX 3090 检测评分记录：graspnet_torch 正视 topK20 覆盖率 30–50%，tilt35°/topK40 为 40%，后者命中竖直度 0.85–0.94。代码中的 0.4 门保留了这个历史基线，不是当前模型/相机/夹爪的新结果。

2026-09-30 的执行记录曾记载 23 单测、触碰后滑开及 Allegro 调优；当前 test/ 不包含这些行为套件，当前执行链与夹爪亦已变化，不能延用“全链通过”结论。gripper_contact_test 是另一个主动仿真探针，其源码存在不等于本轮已通过。

本轮仅阅读 launch、生成器、布局、评分器、执行器、描述辅助和接触探针；未运行 Gazebo、运动或评分。YCB 来源及许可见 models/；包体 Apache-2.0。
