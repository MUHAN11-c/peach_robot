# Peach 项目文档

当前交付入口：[v1.0.0 发布说明](releases/v1.0.0.md)、[版本变更](../CHANGELOG.md)与[完整包恢复](../README_PACKAGE.md)。该版本稳定范围为 amd64 CPU 的 mock / 冻结回放，现场硬件和长期验收继续单独判定。

本目录提供 Peach 生产项目的专题导航、ADR 与带日期的验证记录，范围为 `src/peach`、`src/serial_force` 及 Web 共用的 `src/ros2_web_link`。2026-11-06 按当前源码核对；系统现状以包级 [architecture.md](../src/peach/peach_bringup/doc/architecture.md)、[io.md](../src/peach/peach_bringup/doc/io.md) 与接口清单为准。`src/peach_sim` 是独立子工作区，Gazebo 当前暂停，不计入生产采摘验收。

部署说明同步至 2026-11-07：[自动部署与零环境验证](../scripts/deployment/README.md)、
[打包与恢复](../README_PACKAGE.md)、[部署过程记录](deployment-validation-20261107.md)。
本轮独立 Ubuntu Base 环境完成 45 包构建、35 项 Python 固定版本核对、HTTP 五页浏览器 28 项、
只读 ROSbridge 状态投影和单果 L6 mock 干跑；工具关闭，批次由夹具主动取消。
原生 WS 网页抓取、真实硬件与长期稳定性须另行验收，结论及证据见[验证章节](architecture/05-verification.md)。

## 阅读顺序

1. [总体架构](architecture/00-overview.md)
2. [包依赖](architecture/01-package-graph.md)
3. [运行数据流](architecture/02-runtime-flow.md)
4. [感知与推理](architecture/03-perception.md)
5. [力传感与仿真源](architecture/04-force.md)
6. [验证与证据](architecture/05-verification.md)
7. [数据记录](architecture/07-recording.md)
8. [错误码](architecture/08-failure-codes.md)
9. [Web 后端](architecture/09-web.md)
10. [日志规范](architecture/10-logging.md)
11. [Orin 部署档案](architecture/11-orin.md)
12. [全功能回归矩阵](architecture/12-regression.md)
13. [参考来源](architecture/13-references.md)
14. [全栈适配性评估](architecture/14-adaptability-review.md)
15. [维护与待验证事项](architecture/06-roadmap.md)

验证章节记录对应日期的结果；本次文档同步不构成新的功能验收。自动 10×30×1800 全量回归仍按测试文档记录未通过；Orin NX 未实测。2026-10-13 旧 Wiki、未实施 ForceSeat 计划和无调用的历史源码副本仅在原工作区 `_archive/source_docs_2026-11-06/` 保留，精简交付未携带。2026-11-06 的版本和恢复记录见[历史交付说明](deployment-20261106.md)，当前操作以部署脚本说明为准。

## ADR

- [包边界](adr/0001-package-boundaries.md)
- [GPL 参数](adr/0002-gpl-parameters.md)
- [FastAPI Web](adr/0003-fastapi-web.md)
- [单一录制](adr/0004-recording.md)
- [FSM 不迁移 BT](adr/0005-fsm.md)
- [独立进程](adr/0006-process-model.md)

## 工作区其他源码

完整导航见 [工作区 README](../README.md)。IVG 12 包在 [独立栈导航](../src/ivg/README.md)，仿真六包在 [peach_sim](../src/peach_sim/README.md)，标定与相机分别见 [标定包](../src/aubo_hand_eye_calibration/README.md) 和 [Percipio](../src/percipio_camera/README.md)。这些文档描述当前实现与已知缺口，历史结果不作本轮运行验收。只读驱动文档的旧路径/IMU/octomap/标定字段差异集中记在 [整栈架构](../src/peach/peach_bringup/doc/architecture.md#只读驱动文档的现状差异)，驱动文件本身不改。

## 部署与版本记录

- [部署指南](../scripts/deployment/README.md)：环境准备、自动构建、mock 与隔离验证。
- [打包与恢复](../README_PACKAGE.md)：交付内容、迁移和校验方式。
- [v1.0.0 版本说明](releases/v1.0.0.md)：支持范围、已知限制和验收依据。
- [部署验证过程](deployment-validation-20261107.md)：从零环境安装的发现、修正与原始证据。
- [GitHub 上传发布过程](releases/v1.0.0-github-publication.md)：提交、标签、附件和远端校验记录。
