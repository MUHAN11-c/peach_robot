# sim_system_tests 验证接口

没有 ROS topic/service/action、参数或 console script。colcon 的公共入口是 test/test-result，输出由子工作区 build/log 管理；lint 退出状态只说明对应静态检查结果，不是 harvest 成功数。

有界运行由项目 scripts/sim run / run_session.py 负责，阶段 JSONL、传感器/实体接触证据、action result、进程组清理与 summary.json 属于该会话。离线 analyze_session.py 另写 verification.json；其门控和诊断统计见 [系统接口](../../sim_bringup/doc/io.md)。这些脚本不被本包 CMake 自动执行。

此 doc 目录是源码维护说明，当前 CMake 没有显式安装 README/doc。运行授权、环境和暂停边界见 [项目 README](../../README.md)。
