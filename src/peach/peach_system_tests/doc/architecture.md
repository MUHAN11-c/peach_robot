# peach_system_tests 架构

## 职责

手工复核包：冻结相机回放、有限时探针和场景查询。自动检查只剩官方 ament lint。

## 源码地图

`CMakeLists.txt`：官方 `ament_lint_auto`。`scripts/`：有限时驱动、探针、场景查询和冻结回放。`launch/`、`config/`：回放组合与专用 overlay。

工作区级 `scripts/deployment/` 独立提供安装、构建、只读 mock 探针和 Ubuntu Base 根文件系统验证，
不进入本包 `CMakeLists.txt` 或 `colcon test`。默认验证关闭使能；`--web-e2e` 使用 HTTP fixture，
另做 allowlist 内的只读 WS 投影；`--grasp` 显式调用本包冻结 wrapper 做工具关闭的单果干跑。
验证器默认域 181；冻结 wrapper 沿用环境中的 `ROS_DOMAIN_ID`，未设时默认 81。分阶段输入输出和退出码见
[io.md](io.md)，复现方式见[部署说明](../../../../scripts/deployment/README.md)。

## 入口、输入输出与参数

不进入产品 launch。安装脚本用 `ros2 run peach_system_tests <script>`，参数先看 `--help`；每个入口的 ROS 请求、产物和退出码边界见 [io.md](io.md)。`run_live_camera_mock.py` 默认托管RViz，使用bringup同一应用显示配置；`--no-rviz`用于无头排障。业务配置来自产品默认或 `--task-params-file`，与real同源，不生成高速/放宽超时专用overlay；运行策略由 `--reconstruction` / `--no-reconstruction` 显式选择，不自动ACK。任何模型/抓取失败或恢复等待停止后续；PICK_ALL按全部目标终局验收。模型、动作、soak与清理分别记录实际结果，历史短测数据见testing.md，不视为当前统一参数通过。

## 生命周期、并发与失败

手工起栈时自己选一个空闲 `ROS_DOMAIN_ID`。Jazzy controller_manager spawner 的锁位于 `$ROS_HOME/locks`，不随 DDS 域隔离；不要删其他会话的锁。runner 拥有的进程必须收口，仍须核对残留。runner 非零、skip 及 action 结果未知要分别看日志；不能把进程退出 0 直接记为采摘成功。

冻结 wrapper 会保留强制终止、异常退出和残留 PID 的清理诊断，并退出非零；没有残留不代表正常收口。
冻结驱动是有限时进程，正常返回 0 后由 wrapper 显式声明已完成；其进程组仍归 wrapper 清理。
未声明完成的长驻栈即使提前退出 0 也记异常，驱动非零退出同样不能被正常完成声明放行。
离线分析 `summary.json` 的 `motion_completed`、周期时长/构成、各批完成率、周期 CDF 和空间图完成着色统一只计 `SUCCEEDED` 且完成等级至少 L6；L2 不算完整运动周期，缺失终局不标完成。终局分布仍保留所有等级，以“目标成功”表示 SUCCEEDED；L7 与真实剪切验收仍须分开。

## 验证与限制

`colcon test --packages-select peach_system_tests` 只跑官方 lint。接线与现场验收见 [测试指导](testing.md)，系统组合见 [bringup架构](../../peach_bringup/doc/architecture.md)。跑完清本轮进程；真机运动或 SetIO 需另授权，驱动只读，numpy 固定 1.26.4。lint 通过不证明现场精度、功能安全或剪切成功。

2026-11-07 Ubuntu Base 验收使用 CPU，单果达到 L6，夹具取消后的批次不是全部目标成功。
该轮完整过程与失败记录见[部署记录](../../../../docs/deployment-validation-20261107.md)；
不覆盖原生 WS 网页抓取、真实硬件或长期稳定性。
