# sim_harvest 架构

2026-11-06 源码快照：默认数据驱动小果园，按 2026-11-02 要求仅代码和离线核对，Gazebo 动态行为待验收。本包不连接真机，不调用 SetIO，消费标准 Nav2/MoveIt/Gazebo 服务与现有 Peach IDL。

## 源码与安装入口

- `mission_node.py`：sim_mission、依赖就绪、站位计划、导航/观察/选果/Pickup 串行编排、任务结果；`run_harvest.py` 是显式 action 客户端。
- `grasp_node.py`：sim_grasp、Pickup 受理、底盘停车、PlanningScene/ACM、模型许可、实体替换、持果、搬运和入筐证据。
- `survey.py`：附着在 GraspNode 的 SurveyScene 与限定 harvest_stow 的 MoveTo，复用同一把臂锁和操作租约，不另起节点。
- `vision_target.py`：BeginScene、稳定视觉 ID、BuildTargetModel、精确时刻 TF、模型摘要；此适配器不读取实体清单。
- `operations.py`：MoveGroup/服务/action 有界等待、取消、POSIX operation.lock 与 JSONL；`base_guard.py` 在 CollisionMonitor 之前实现底盘速度门。
- `setup.py` 安装上述 Python 包、README/doc，并注册 grasp_node/base_guard/mission_node/run_harvest；package.xml 与 resource/setup.cfg 提供 ament 依赖和脚本配置。test/ 只有官方 flake8/pep257 包装。

## 决策与操作

`MissionNode` 导航到树级观察站，调用 SurveyScene 移动并核验腕相机视点；BeginScene 使用树级稳定 scene_key，按观测稳定 ID 选果并 BuildTargetModel。已采记录按该场景的视觉 ID 去重，不用固定空间半径吞掉相邻果。目标额度按采收颗数计算，每站可以重复观察；无可采观测时经 MoveTo 收臂后前往下一站。视觉指定实体请求明确拒绝。

`VisionTarget` 不访问实体清单；仅接受确认/当前观测/几何 ACCEPT 的候选，精确曝光时间 TF 变到 map。重建身份、版本、工具档案、有效期及全部所需阶段能力必须有效，缺失不回退真值。标准 Grasp.id 携带模型身份元组哈希，执行侧从现有 GraspDecision 校验完整身份，在 approach、insert、cut 前分别复核许可和有效期。

`GraspNode` 在操作边界将视觉位置关联到唯一可删除实体；门限8cm且最近两个候选间须有2cm差距，否则拒绝。不会用实体位置改写视觉抓取位姿。默认 data_orchard 的枝干圆柱和未采邻果盒来自同源 manifest；旧 orchard manifest 当前没有 obstacles 字段，不能据此声称已把其全部树干/枝条装入规划场景。仅当前目标对工具接触链放行，保留机器人原 ACM，事务结束恢复。Pick/Survey/MoveTo 共用一把臂锁和进程操作锁；底盘停稳后才允许臂动作。

Mission 的准入检查隔离标识、use_sim_time、最近 clock/joints、AMCL/bt_navigator Active、JSB/JTC Active、Nav2/Pickup server 及恢复态；Survey/MoveTo 的可用性在派发时等待，不在这份准入快照里预先保证。导航还要求 SRDF harvest_stow 关节误差小于 0.08 rad；成功后用新鲜 odom 连续静止超过 1 秒核验停车。Grasp 的独立准入另检查 sandbox 标识、包含 GazeboSimSystem 的模型文件、MoveGroup 与 create/remove 服务，操作前关闭 base guard 并核对至少 0.5 秒实际停车。两份 ready() 检查项不同，不能统称为全部依赖已经验证。

## Pickup 的实际执行几何

Mission 将目标 bag_bottom 放入标准 Grasp.grasp_pose，沿目标轴构造完整姿态。Grasp 取该姿态作为接触终点，预接近点为终点沿工具 Z 轴后撤 0.12 m；OMPL 到预接近点，Pilz LIN 到袋底，撤退沿原 LIN 回预接近点。此实现没有按 TargetModel.cut_pose/cut_travel 再运动到袋颈，也不执行真实刀具开合。视觉目标的 `entry` 当前同样取模型 bag_bottom。

MoveGroup 直接执行（plan_only=false），普通段 OMPL/RRTConnect，直线段 Pilz/LIN；缩放为仿真适配层的 0.25，不是现场真实采摘的默认速度。落筐姿态先枚举筐中两个落点、多个高度和偏航角，必须碰撞感知 IK 成功；额外无碰撞约束 IK 只用于碰撞诊断，不能进入执行。

## 物理与失败

独立袋果由同一网格的静态/动态副本表达采前/采后。先核验实际 Gazebo 机器人位姿与当前臂 TF 合成的 TCP 距目标袋底不大于 4cm，再 create 动态副本、等 attached，随后 remove 树上静态实体；该顺序完成后才记 cut_confirmed 并同步 MoveIt 附着物。释放等待 detached，移除腕部附着物，再检查实际入筐。

入筐判定把袋果完整碰撞盒的八角变换到机器人系，要求落在代码规定的筐内范围、位姿新鲜、释放之后有新鲜筐接触；连续新观测速度低于 0.04m/s 满 1 秒才通过，最多等待 12 秒。随后把实测负载登记成 MoveIt 中附着于筐的规划对象，收臂后再做一次稳定核验才记 harvest_confirmed。Gazebo 果实在筐内仍是自由刚体，规划附着不表示物理上固定到筐。只有这些阶段全部满足才计成功；这是刚体采剪抽象，不是刀刃力学、柔性枝条或摩擦抓取。

现有筐与落点实现容量至多两颗。结算区分额度、容量、比例和场景耗尽；未实现卸筐。历史第二颗入筐失败尚无本轮动态复测证据。切断/持有不确定时禁止下一次导航，需恢复场景。取消向依赖传播，迟到/未确认取消进入恢复状态，不恢复旧轨迹。

Operations 对已接受 action 的失败请求取消：最多等取消回执 5 秒、终态 8 秒，未确认则置 recovery_required；等待受理失败也保守进入恢复态，迟到受理会补发取消。service 已派发后的副作用不是可抢占事务；Grasp 在发出 create/remove 前就记副作用风险，取消或失败后保持恢复门。已创建且尚未发 remove 的动态副本会尝试删除回滚，但不因此抹去不确定性。ACM 恢复失败也保持恢复门。普通 reset/重派没有恢复物理场景的实现。

构建和官方 lint 不替代视觉、IK、规划、落筐与取消链的有限时运行验收。
