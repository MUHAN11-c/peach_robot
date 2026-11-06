# 维护与待验证事项

架构事项按 2026-11-06 源码整理，部署进展同步至 2026-11-07。包级活文档记录实现，带日期的运行结果见 [验证与证据](05-verification.md) 和 [回归矩阵](12-regression.md)。

部署脚本与 Ubuntu Base 隔离环境已落地：45 包构建、35 项固定依赖、HTTP 网页 28 项、只读 WS 状态投影和单果 L6 mock 通过，过程与修正见[部署记录](../deployment-validation-20261107.md)。后续应用源码变更应新建零环境；`--resume` 仅用于本轮安装/构建修正。以下待验证事项仍分别判定。

1. 参数：生产能力、观测和 bringup 辅助节点使用 GPL；独立 vegetation 保留 `attach`。升级生成器后重新检查整数范围与回调先后语义。
2. 错误码：维护 FailureCode 稳定值；保留旧事件文本兼容，逐项审查纯核中剩余数值而不凭字符串猜语义。
3. Web：整栈默认 SDK/ROSbridge + 同源 HTTP；HTTP 调试门、审计与 ROS 节点最终授权的范围须分别验证。
4. 记录：会话 bag 由 observability 单写者维护；力分段仅兼容读取历史 sidecar，当前没有自动分段写者。
5. 性能：x86 历史基准不能替代 Orin 实测；TensorRT/Orin 验收仍待目标机。
6. 回归：按受影响包官方检查和手工 mock/replay 验证；感知已有图像解码 pytest 不扩展为新行为套件。10×30×1800 未通过，不能用短测补成通过。
7. 归档：旧 Wiki、会话转录、未实施 ForceSeat 与未安装的 sim_perception/vision 快照已归档，原路径/校验见工作区 `_archive/source_docs_2026-11-06/manifest.json`。
8. 部署边界：原生 WS 网页抓取、真实硬件和剪切须单独验收；旧 IVG dashboard 依赖缺口、此前只读驱动 7 项 lint 检查失败和 70 个 cppcheck skip 保留，不以 mock 部署结果冲销。精简交付不附带上述本机归档。

Gazebo 当前暂停；仿真子工作区的离线文档整理不表示恢复运行授权。
