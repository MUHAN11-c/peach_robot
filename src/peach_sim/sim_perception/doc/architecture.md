# sim_perception 架构

2026-10-29 起本包收窄为仿真配置覆盖和兼容入口；当前按 2026-11-02 要求暂停 Gazebo，
业务算法只有现行 Peach 能力包一份实现。

`sim_bringup/launch/perception.launch.py` → 共享全量配置 + 本包仿真 overlay + 最终共享工具/停位/运行目录覆盖 →
`sim_scene_perception_node` / `sim_target_reconstruction_node` → 目录外既有能力
的 `main(args=None)` → 同名 LifecycleNode。共享包与权重只读。

本包仅安装 `sim_perception` 根包里的两个入口；未安装的 `vision/` 历史快照
已移入工作区 `_archive/source_docs_2026-11-06/`，没有现行外部调用方。停位几何从
`peach_common/config/grasp_standoffs.yaml` 读取，工具档案来自 `aubo_description`；本包不维护有效的本地停位副本。生命周期管理与 bond 策略
由组合包负责；本包不创建第二套 lifecycle、TF 或参数框架。

仿真覆写范围是推理阈值、采集窗口、深度边界与仿真 ICP 开关；参数合法范围
以共享能力的当前 schema 为准。仿真不修改真机参数。模型从
`peach_scene_perception/model` 解析，运行记录根由 launch 强制指定为项目内路径。

实际启动脚本仅在函数内导入两个共享 main 并透传 args；setup.py 仅安装这两个入口所在的根 Python 包和两份 overlay。共享算法、生命周期/诊断/取消由能力包维护。仿真分割器由 overlay 明确改为 MobileSAM，重建关闭 ICP，具体覆盖与追溯标签限制见 [README](../README.md)。

官方 lint 仅覆盖实际安装的适配面；视觉行为由独立 `vision` 运行日志验证。


## 2026-11-02 仿真 overlay

收集窗回到共享能力的 4 个累积帧、2 个稳定帧、12s基准，避免将60帧收齐当作视觉成功。相机标定身份显式标注 Gazebo 理想640×480/63°/米制深度与当前xacro手眼链，不冒用真机标定标签。模型能力、有效期、配置与工具身份由 sim_harvest 选择/执行边界复核，无法获得有效许可时不回退真值。用户当前仅要求离线核对，未宣称运行端点或视觉闭环通过。
