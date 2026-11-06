# 验证与证据

本页按日期区分验收结果。当前执行方法见[系统测试指导](../../src/peach/peach_system_tests/doc/testing.md)，
部署入口见[部署脚本说明](../../scripts/deployment/README.md)。2026-11-07 的文档同步未重跑功能测试。

## 2026-11-07：独立 Ubuntu Base 部署与 mock 验收

从无 ROS、Node、colcon、venv 和编译产物的 Ubuntu Base 24.04.5 根文件系统开始，
经 apt/pip/npm 安装依赖。过程中修正脚本并显式续跑，未导入宿主机依赖或构建缓存；
环境共享宿主内核，运行阶段使用独立网络命名空间且仅有 `lo`。

| 范围 | 本轮结果与边界 |
|---|---|
| 构建与依赖 | 45/45 ROS 包；35 项 Python 固定版本匹配，pip check 无冲突；SDK 类型与两套网页资源构建通过 |
| 默认只读 mock | GenericSystem、3 控制器、4 生命周期节点、关节顺序及对应数值、RGB-D/点云和 PlanningScene 服务通过；所有使能关闭 |
| Web | 六路 HTTP 200；五页 HTTP fixture 浏览器 28 passed / 0 failed，四档屏宽；中文字体补齐后截图已复核 |
| ROSbridge | allowlist 内 web_state 两帧只读订阅通过；不代表网页原生 WS 服务/Action 抓取验收 |
| 显式单果干跑 | request `deploy_acd92bb0b3f3`，target_1 达 L6、tool=false、回放暂停；target_2 被几何质量门拒绝 |
| 批次终态 | 夹具主动取消，Action=CANCELED、result.success=false；单果 succeeded=1、wrapper exit=0，非全部目标成功 |
| 录包与收尾 | 最终两份 bag 14868/9848 条完整读回；失败轮一起共四份均可读；自有进程无残留、8090/9090 未监听 |

问题经过、最终日志及 JSON 入口见[部署过程记录](../deployment-validation-20261107.md)。
原始机器汇总为 `runs/analysis_reports/deployment_20261107/clean_room_summary.json`；
详细证据保留在本机 `clean_room_20261107/`，不随文档补充包携带。

新部署脚本的 flake8/pep257 与 Shell/Node 语法检查通过。此前全包检查仍有只读 AUBO 驱动
7 项 lint 检查失败、70 个 cppcheck 用例跳过，两轮结果分别保留。
真实机械臂、相机/串口、SetIO、真实剪切、Gazebo、Orin 与 10×30×1800 长测未由本轮验证。
旧 IVG dashboard 的 ros_web_link/共享 JS 缺口仍在。

## 2026-10-27：历史已执行项

以下保留原日期的命令、数据与证据，没有在本轮重跑硬件验收。

### 构建/测试

```bash
colcon build --packages-select peach_common peach_vision_core peach_scene_perception \
  peach_target_reconstruction peach_supervisor peach_scene_obstacles \
  peach_arm peach_bringup peach_system_tests peach_harvester
colcon test --packages-select peach_common peach_vision_core peach_scene_perception \
  peach_target_reconstruction peach_supervisor peach_scene_obstacles \
  peach_bringup peach_arm
```

结果：10 包构建成功；新包官方 lint/测试通过；`peach_bringup`/`peach_arm` lint 通过；接口清单通过。

### 真实相机 + RViz

```bash
run_live_camera_mock.py --models 0 --rounds 0 --soak-seconds 20 --domain 101 --rviz
```

- camera/depth/joints fresh，`rviz_alive=true`；
- scene/reconstruction/supervisor/arm Active；
- scene 干净退出；
- `residual_pids=[]`；
- runner `passed=false` 仅因 `move_group` 退出 `-11`。

### 感知基准

`benchmark_perception.py`：13.84 FPS，p50 72.83 ms，5 检测/4 候选。

### 力仿真

- `force_sim_node` + static `base_link→tcp`；
- `/force/sample --once` 返回完整 5 通道帧；
- `serial_force` lint 通过。

## 2026-10-27 历史证据路径

- `runs/peach_refactor_20261027/phase1.md`
- `runs/peach_refactor_20261027/live_camera_rviz2/run/report.json`
- `runs/peach_refactor_20261027/live_camera_rviz2/run/stack.log`

## 2026-10-27 历史补充回归（不替代 10×30×1800）

- 14 包构建；10 包官方 lint/test 全通过。
- 接口清单 59 active + 5 reserved。
- 校准身份单轮：`model_count=1`、`target_1`、`success=true`、`pregrasp_completed=true`。
- 真实相机 15 s soak：4 目标、camera/depth/joints fresh。
- 感知基准：13.74 FPS，p50 71.87 ms，p95 78.90 ms。
- 唯一失败：外部 `move_group` shutdown `-11`；`residual_pids=[]`。自动 10×30×1800 仍按 `testing.md` 记录未通过。
