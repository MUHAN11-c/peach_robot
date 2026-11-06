# sim_harvest 接口

- `/sim_harvest/run_harvest`：现有 `peach_interfaces/action/RunHarvest`；视觉模式 PICK_ALL + 空 target_ids；真值模式可指定实体。max_targets 是节点部署参数，按果数限制，0表示容量范围内不限，当前总容量2。正常结算且至少采一颗时 success=true；若之后任一阶段失败/取消，本次 result.success=false，已经成功的计数仍保留。termination_reason 区分 target_limit_reached/basket_capacity_reached/target_ratio_reached/scene_exhausted/no_targets_succeeded，异常则返回具体原因。
- `/sim_harvest/pickup`：标准 `moveit_msgs/action/Pickup`。一个 map 系 Grasp；真值 target_name 为实体ID，视觉为观测ID。视觉 Grasp.id 是 run/epoch/目标/模型/工具/标定/配置/有效期的身份哈希，最终动作必须与当前 GraspDecision 一致。
- `/sim_harvest/survey_scene`：现有 SurveyScene，按相机位置/朝向规划观察 TCP，不指定某颗真值。观察完成不代表已经检测到果实。
- `/sim_harvest/move_to`：现有 MoveTo，目前只支持 KIND_NAMED + harvest_stow，验证到位后返回；用于空站后安全换站，不开放通用额外运动源。
- `/peach/perception/target_observations`、BeginScene、BuildTargetModel：视觉发现和重建来源；`/peach/reconstruction/grasp_decision` 提供阶段许可；接口权威仍是现有 IDL。
- `/sim_harvest/events` JSON阶段证据和运行目录 sim_mission.jsonl/sim_grasp.jsonl；实体、连接、筐接触证据同系统接口文档。详见 [系统接口](../../sim_bringup/doc/io.md)。

部署参数 manifest_file、stations_file、run_directory、robot_description_file、tool_profile、perception_mode、use_sim_time；Survey 参数 survey_camera_position、survey_look_at 为平台系米制向量。仿真参数不写入目录外 Peach/驱动配置。

## 模型与阶段许可

visual_model_identity 将 run_id/harvest_run_id、scene_epoch、target_id、model_revision、tool_profile_id、calibration_revision、config_revision、valid_until 的 sec/nanosec 序列化后取 SHA256，前缀 sha256:。它不包含 algorithm_version、generated_at 或几何坐标，不能称为整条模型消息的摘要。

VisionTarget 先要求 Build success、model.accepted、ID/epoch/source_run 匹配、revision/标定/配置非空、至少一机位、工具档案一致且尚未到期；geometry/pregrasp/sleeve/cut 四能力必须全为 VALID。模型 header 为 finalize 时间，因此 map 变换改用 source_end（最后积分曝光），禁止零 stamp 或 latest TF。

Pickup 每次在 approach/insert/cut 前从当前 GraspDecision 复核该摘要、身份和有效期：所有阶段要求 geometry/pregrasp VALID，insert 再要求 sleeve VALID，cut 再要求 cut VALID。没有把 allowed 或径向/轴向余量作为这些复核的替代条件；也不签发真实机器人的运动授权。ground_truth 模式不执行这条视觉许可链。

## 结果、互锁与超时

RunHarvest 的 per_target_timeout_s 限定等待 Pickup 结果，缺省 240 秒，不包含此前导航、Survey 或 Build 的全部时间；导航默认 120 秒，观察/收臂派发各 90 秒，视觉锁定/建模默认 90/180 秒。Operations 的服务发现、action 受理、取消和回执另有等待预算，不应把任一值称为整任务硬墙钟上限。Action 完成必须同时核对 ROS 终态和返回的业务字段。

BaseGuard 50ms 使用主机 steady timer 更新：arm_busy、恢复态、收臂超差或 clock/joints 超过 1 秒均锁底盘；只有未锁且末条速度命令小于 0.5 秒才透传。base_locked 只反映该逻辑门，实际停车由 odom 另查；关节检查是最近位置与 SRDF 的差，不是驱动授权或硬件急停。

状态/目标/互锁 Bool 使用 RELIABLE/TRANSIENT_LOCAL depth1；events 用 RELIABLE/VOLATILE depth10。Gazebo attached/detached 与实体位姿/接触订阅为普通流，不能假设迟到订阅能收到历史状态。完整桥名和实际实体证据见 [系统接口](../../sim_bringup/doc/io.md)。

用户当前要求暂不运行 Gazebo；本轮仅离线验证，不宣称这些运行端点已被实测。
