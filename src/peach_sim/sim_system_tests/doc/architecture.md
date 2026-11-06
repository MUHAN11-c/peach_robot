# sim_system_tests 架构

这是 ament_cmake 的官方 lint 汇集包，没有运行节点、Python 业务包或行为测试。CMakeLists.txt 在 BUILD_TESTING 下调用 ament_lint_auto_find_test_dependencies，并预置 copyright/cpplint 已发现标记；package.xml 仅声明 ament_cmake 与 ament_lint_auto/common。LICENSE 和 README 提供许可及验证边界。

项目 scripts/sim 的 test 分支选择六个 sim 包并读 test-result；本包不负责拉起 Gazebo、Nav2、MoveIt 或客户端。scripts/check_models.py、analyze_session.py，以及 sim_worlds/reconstruction 的 Blender 检查器属于独立开发/证据工具，未注册为本包测试。

Gazebo 当前暂停。历史日志和离线结果不能通过增改本包测试说明自动转化为当前动态验收；恢复后的运行链、取消、模型与入筐证据分别按 [sim_bringup 架构](../../sim_bringup/doc/architecture.md) 核对。
