# ivg_graspnet

点云 6D 抓取检测与独立 MoveIt 接近，不进入 Peach harvest_system/lifecycle，也不消费 peach_interfaces。默认后端 graspnet_torch 使用随库 GraspNet-baseline 权重和纯 torch 点云算子；另有 contact_graspnet 适配器。不依赖 AnyGrasp SDK，但仍依赖各后端模型和权重。

## 公共入口与数据链

`graspnet_detect.launch.py` 只启动 graspnet_demo_points_node，不启动相机、TF 或 MoveIt。显式参数为 backend（默认 graspnet_torch）、model_path（默认 share/models/checkpoint-rs.tar）、workspace（默认空）。其余参数来自 config/graspnet.yaml。点云默认 `/camera/depth_registered/points`，frame 为空时回退 camera_depth_optical_frame。

检测默认不采集，`/graspnet_capture_control`（SetBool）开启后默认收集 3 组，定时器每秒检查是否可推理。后端产生原始 GraspList，经开口裁剪、碰撞过滤、NMS、排序/top-K 后发布 MarkerArray、PoseArray、TF。输出 stamp 取最近输入点云，坐标转换查询 latest TF，不能理解为同 stamp 的精确变换。

- `backends` 注册表隔离模型实现，`grasp_core.GraspList` 保存 17 维抓取向量。
- `postprocess.run_postprocess` 与 GripperGeometry 处理模型无关的几何规则。
- `InferenceSession` 解析 device、fp16/autocast 和显存摘要。
- 默认权重配套 checkpoint-rs.yaml 记录网络结构参数。contact_graspnet 的 model_path 是 checkpoint 目录，切换时必须同时指定有效目录，不能沿用默认 .tar 文件。

`graspnet_grasp.launch.py` 组合检测与 publish_grasps_client，显式参数只有 workspace、grasp_poses_topic、planning_group（manipulator_e5）、ee_link（grasp_tcp）、base_frame（base_link）。backend/model_path 应在 detect 入口配置。当前 grasp_poses_topic 只覆盖客户端；被包含的 detect launch 没有声明/转发该参数，非默认话题须同时核对检测节点配置。

## 执行客户端的实际边界

publish_grasps_client 的 require_enable 默认 false；main 启动后立即 run 一次，收到足够数据即可选择位姿、补偿 TCP 并发起接近。它不控制夹爪 IO，也不执行完整抓取放置。选择按抓取轴的双向竖直程度 `abs(dot)` 排序，不区分朝上/朝下。

require_enable=true 只在 run 入口检查本地使能值；初值 false 时直接返回并退出，不是常驻等待 enable_grasp_motion 服务的待命模式。执行开始后也没有持续撤销使能检查。该开关不能替代运行授权或运动取消。

apply_grasp_z_flip 默认 true。BackendInfo.approach_flip_z180 当前只用于检测节点日志，不会自动配置执行端；切换后端时须人工同步该节点参数（launch 未透传）。contact_graspnet 的方向约定仍待实物核验。

GraspMotionController 默认末端 grasp_tcp：先尝试 XY 高位平移 → 转姿态 → Z 下降的笛卡尔路径；完整路径且点数不超过 60 时执行，否则回退 MoveGroup 位姿目标。已有受理 goal 的结果等待超时会发 cancel_goal_async；goal 受理等待超时和 GetCartesianPath 服务超时不具备相同的取消保证。

真机运动须操作员明确授权；启动 real 栈或收到 PoseArray 均不构成授权。本包不包含 Peach 的接触/clearance/FSM 防护。

## 依赖与验证记录

torch/torchvision/scipy 等使用工作区 aubo_py3.12 环境；contact_graspnet 还依赖 trimesh。上游抓取库和模型分别见库内许可文件，本轮不改动 vendored 实现或权重。

当前 test/ 只有官方 ament flake8/pep257 检查。2026-09-29 campaign 报告中的等价门与 contact_graspnet 221 抓取属于历史记录（报告已于 2026-10-10 清理，可查 git 历史），不代表当前版本结果。2026-11-06 本轮仅静态核对，未启动检测或运动。
