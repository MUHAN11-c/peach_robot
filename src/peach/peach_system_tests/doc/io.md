# peach_system_tests 输入输出

本包安装人工检查工具，不注册产品节点或自定义 IDL；`colcon test` 仅运行
`CMakeLists.txt` 的官方 ament lint。详细步骤与结果口径见 [testing.md](testing.md)。

## 已运行栈的工具

- `drive_harvest.py`：向 `/peach_supervisor/set_enables` 和 `run_harvest`
  发送请求；默认设置 execution=true、tool=false，`--grasp` 决定抓取使能。
  `--skip-enables` 仅跳过使能写入，仍发送 goal。退出 0 要求 Action SUCCEEDED
  且 result.success；该通用驱动没有 mock 模式核验，也不负责停外部栈或复原使能。
- `probe_topics.py`：有限时订阅指定 Image/PointCloud2，默认 RELIABLE，
  `--no-reliable` 可作 BEST_EFFORT 对照。打印计数/平均到达率/末次规格；
  即使全零也返回 0，须检查 `ALL_TOPICS_ZERO` 和实际计数。
- `check_planning_scene.py`：只读 `/get_planning_scene`，打印世界对象和 ACM；
  服务缺失或超时返回非零，查询成功的 0 不代表所有条目符合预期。

## 托管 mock 夹具

`run_frozen_grasp.py` 组合冻结 launch 与 `drive_frozen_grasp.py`；bag 只读，
重发节点提供相机/点云与 `/frozen_camera_replay/pause`。驱动核验 mock 插件和
暂停服务，再写夹具参数/使能并发 PICK_ALL；第一颗终局后取消自己的批次。
退出 0 按单果 summary、暂停与墙钟条件判定，不要求自然完成全部目标。
`--skip-launch` 不停止外部栈，wrapper 只收尾自己的 request 与进程组。
驱动正常返回 0 属于有限任务完成，收尾时不作为栈提前退出；任何非零驱动结果、
长驻栈提前退出、强制终止或残留进程仍导致 wrapper 非零退出。

`run_live_camera_mock.py` 启动真实 stereo 相机与 mock 臂，核验启动事实，
通过原生 ROS 服务/Action 和 8090 快照采样。`--reconstruction` 与
`--no-reconstruction` 选择本轮策略，`--models>0` 必须启用重建；作业参数来自
产品默认或 `--task-params-file`。本轮默认不重建、models=0、PREGRASP_ONLY，
工具始终关闭，不自动 ACK。报告、快照、日志、进程退出/清理证据及
`records/{session_*,<request_id>,…}` 写入独立 `--output`；默认域 86。

## 离线工具

`benchmark_perception.py` 读取 RGB-D `.npz` 并实际运行模型，输出官方推理周期
与整段墙钟统计。`gen_baseline_inventory.py` 导出当前 YAML 叶值、接口名和函数索引，
不比较历史快照。`analyze_harvest_record.py <run> [--out …]` 读取记录并生成 PNG、
CSV、`summary.json`；默认输出 `<run>/analysis`，完整运动周期只计 SUCCEEDED 且 L6 以上。

## 工作区部署验证器

这些入口在工作区 `scripts/deployment/`，不安装为 `ros2 run peach_system_tests` 工具：

| 入口 | 输入、操作与输出 |
|---|---|
| `deploy.sh` | 读取 requirements.txt、npm 锁与源码；可选 apt 安装，生成 venv、网页、install、部署日志与 `deploy.exit`；`--verify` 才运行 mock |
| `verify.sh` / `verify_mock.py` | 加载部署环境与最小 bag，启动自有 mock 栈；查询插件、控制器、生命周期、关节、图像/点云、PlanningScene、HTTP 和 WS 投影；写 `environment.json`、`verification.json`、分项报告与录包读回结果 |
| `--web-e2e` | 运行 HTTP 五页浏览器套件，可创建关闭执行的调试会话；产出 `web_e2e/report.json` 与截图，不建立原生 WS 抓取结论 |
| `--grasp` | 在实际 GenericSystem 核验后调用冻结 wrapper，显式开启 mock 执行与抓取、关闭工具；产出本轮 request、单果与批次结果及暂停/清理证据 |
| `validate_clean.py` | 读取官方基础镜像及 SHA-256，创建独立 rootfs/workspace；在新网络命名空间运行验证；检查点同步 `clean_room.json`、`process.md` 和唯一阶段日志 |

验证输出使用新目录，默认域 181，需 8090/9090 空闲；结束后清理自有进程，不保留网页服务。
安装、构建、探针、录包或清理任一步失败均返回非零。退出 0 只覆盖本次实际选中的阶段，
不会将单果夹具的批次 CANCELED 改判为整批成功。已有零环境需显式 `--resume`；
续跑只同步部署脚本和依赖，应用源码变更应使用新目录。
参数、路径映射及已实测范围见[部署说明](../../../../scripts/deployment/README.md)。

工具退出码、Action 终态、账本完成等级、相机/RViz 活度和清理结果分别核对；
任一脚本均不替代操作员的真机授权。
