# 2026-11-07 部署脚本与零环境验证过程记录

功能验收完成：2026-11-07 02:44；结果汇总：02:49（Asia/Shanghai）。本轮零环境部署与 mock 功能验收已通过，失败过程及修复证据均已保留。相关入口文档于同日随后同步，未因此重跑功能验收。

## 目标与范围

本轮任务为编写可重复运行的部署脚本，并从无应用依赖的独立环境验证安装、构建与 mock 运行。
上一轮已部署工作区的 45 包构建、网页 28 项和单果 L6 结果只作为参考，不能替代本轮零环境结果。

- 源码工作区：`/home/wjz/peach_robot/aubo_e5_jazzy_ws`。
- 零环境目录：`/home/wjz/peach_robot/clean_room_20261107`。
- 环境内工作区：`/workspace`，对应外部的 `clean_room_20261107/workspace`。
- 驱动、控制器、dashboard 和 ros2_control 模型保持只读；不启动 dashboard 或 Gazebo。
- 只读验证保持所有使能关闭；显式 `--grasp` 才执行 mock 单果干跑，工具仍关闭。

## 已形成的脚本

| 文件 | 作用 |
|---|---|
| [bootstrap_ubuntu.sh](../scripts/deployment/bootstrap_ubuntu.sh) | Ubuntu 24.04 系统依赖、ROS Jazzy 软件源、Node、rosdep 安装 |
| [deploy.sh](../scripts/deployment/deploy.sh) | 隔离已有 shell 环境，创建 venv，重建网页与全部 ROS 包 |
| [env.bash](../scripts/deployment/env.bash) | 加载当前部署的 ROS/install/venv 环境 |
| [verify.sh](../scripts/deployment/verify.sh)、[verify_mock.py](../scripts/deployment/verify_mock.py) | 环境检查、只读冻结回放、可选网页 E2E 与单果 mock 干跑、录包读回与清理 |
| [probe_websocket.js](../scripts/deployment/probe_websocket.js) | 检查 ROSbridge allowlist 中的实时 web_state 投影 |
| [validate_clean.py](../scripts/deployment/validate_clean.py) | 创建 Ubuntu Base 根文件系统，分阶段执行安装/构建/隔离网络验证 |
| [使用说明](../scripts/deployment/README.md) | 新机器部署、零环境复现、日志和结果判定 |

## 零环境的具体定义

基础镜像为官方 Ubuntu Base 24.04.5 amd64，下载地址：
[ubuntu-base-24.04.5-base-amd64.tar.gz](https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/ubuntu-base-24.04.5-base-amd64.tar.gz)。
其固定 SHA-256 为：

```text
e77b6f10c2590cef872b33ee9f635a0e3fd1f57fb074c0e52b5c7f56147a0c86
```

已核对下载文件与官方校验和一致。bubblewrap 创建独立挂载、用户、PID、IPC、UTS 命名空间，
环境内 UID 0 映射为宿主机当前普通用户。宿主机 `/opt/ros`、用户目录、venv、node_modules、
包缓存、build/install 不挂载；只复制源码、模型和最小回放夹具。
内核与宿主机共享，属于独立根文件系统验证，不是另一台虚拟机。

初始断言已通过：环境内不存在 ROS、Node、colcon、build/install、aubo_py3.12 或旧 `.deps`，
也不存在宿主机的 `/home/wjz`。证据为
[empty_baseline.log](/home/wjz/peach_robot/clean_room_20261107/logs/empty_baseline.log)。
安装阶段允许联网；运行验证阶段已启用新的网络命名空间，只启用回环接口，并检查接口列表。
只有单 UID 映射时，fakeroot 用于模拟 apt 包的所有权元数据，运行库仍由环境内的软件包管理器安装。

## 执行与问题处理

| 时间（北京时间） | 事实与处理 | 证据 |
|---|---|---|
| 02:01 | 解压全新镜像并复制纯源码，空环境断言通过 | `clean_room.json`、`empty_baseline.log` |
| 02:01—02:04 | 首次官方 Ubuntu 下载出现 HTTP 502，安装返回 100 | `clean_room_install.log` |
| 02:04—02:06 | 补上 apt 下载重试及显式镜像配置；最小镜像没有 CA，直接使用 HTTPS 失败 | `clean_room_install_retry.log` |
| 02:06 | 通过 Ubuntu GPG 签名验证的 apt 安装 ca-certificates，再切回 HTTPS；证书安装完成 | `bootstrap_tools.log` |
| 02:09 | ROS/Jazzy 与系统依赖正在根文件系统内解包；尚待该阶段结束 | `logs/system.log` |
| 02:12 | fontconfig 安装因单 UID 映射无法设置 staff 组而失败；设置 `FAKEROOTDONTTRYCHOWN=1`，独立探针确认可模拟 `0:50` 所有权，13 个待配置包随后完成配置 | `bootstrap_tools_20261106T181222Z_91397b.log` |
| 02:12 | Node 24.18.0 下载、官方 SHA-256 检查与安装通过；基础 ROS 可用 | `system_20261106T181225Z_56f1d8.log` |
| 02:13 | 对照本机 rosdep 帮助及解析源码，修正多依赖类型选项的重复参数写法；继续安装项目构建与运行依赖 | `system_20261106T181330Z_f71293.log` |
| 02:21 | 在现有工作区实测新验证器：只读回放和浏览器检查完成，但后续端口探针将 TIME_WAIT 误判为占用；该次总体验证返回 1 | `new_verifier_check.log`、`runs/deployment/script_verify_20261107/verification.json` |
| 02:22 | 零环境的系统依赖与主链 rosdep check 均通过；统一入口重复执行系统阶段也返回 0，开始全新 Python 安装 | `system_20261106T182241Z_c4aa55.log` |
| 02:24 | 端口探针改为检查实际监听状态；现有工作区顺序完成只读回放和 L6 干跑，录包读回与清理通过，返回 0 | `new_verifier_fixed.log`、`runs/deployment/script_verify_fixed_20261107/verification.json` |
| 02:26 | 零环境 pip 解析到 setuptools 84.2.1，与 colcon-core 0.21.3 的 `<80` 要求冲突；pip check 返回 1，构建没有继续 | `clean_room_pip_check_before_fix.log` |
| 02:26 后 | 对照已安装包元数据，新增 setuptools 78.1.0 固定版本，同时满足 Torch `>=77.0.3` 和 colcon `<80`；恢复安装/构建阶段 | 本轮 requirements.txt 与新阶段日志 |
| 02:29 | 修正工具链后，pip check、网页类型检查与资源构建通过；全新 CMake 在 Percipio 包缺 camera_info_manager 时返回非零 | `deployment_20261106T182819Z/build.log` |
| 02:29 后 | 核对厂商 CMake 与 package.xml，发现多项未声明依赖；部署脚本显式补齐 5 个 Jazzy apt 包，厂商源码不改 | bootstrap_ubuntu.sh |
| 02:33 | 厂商补充依赖及主链 rosdep 检查完成，恢复统一部署流程 | `system_20261106T183210Z_b5b14f.log` |
| 02:35 | 本轮独立工作区的全部 45 包源码构建通过；35 项 Python 清单与网页构建已安装完成 | `build_20261106T183348Z_214219.log`、部署目录中的 `build.log` |
| 02:36 | Chromium 下载完成；运行验证在新的网络命名空间内开始，只保留回环接口 | `browser_download_20261106T183550Z_6a1d12.log`、`verify_20261106T183610Z_a2e25a.log` |
| 02:36 后 | 网页 28 项功能检查通过，但截图复核发现缺少中文字体，不能作为中文可读性通过 | 首轮零环境 `readonly_mock/web_e2e/monitor_1440.png` |
| 02:36 后 | MoveGroup 因默认 Pilz 插件缺失退出，单果动作等待规划服务；先前只读探针仅检查生命周期，未覆盖此服务 | 首轮零环境 `frozen_grasp/run.log` 中 `LibraryLoadException` |
| 运行问题修正 | 显式补装 Pilz/STOMP 和中文字体；增加插件索引、中文字体和 PlanningScene 服务就绪检查，保留原驱动配置 | bootstrap_ubuntu.sh、verify_mock.py |
| 02:42 | 统一入口的系统安装、35 项依赖安装、网页构建、45 包构建和浏览器准备再次完成，增强后的运行验收开始 | `system_20261106T184138Z_c44797.log`、`build_20261106T184201Z_21d3dc.log` |
| 02:44 | 零环境完整运行验收返回 0：规划服务、只读回放、网页 28 项、单果 L6、录包与自有进程清理均通过 | `verify_20261106T184221Z_5d4596.log`、最终 `verification.json` |

这里的下载失败与缺证书属于本轮实际发现的引导问题。没有关闭 TLS 校验或 apt 签名校验。
脚本已相应修正，原始失败日志保留在
`runs/analysis_reports/deployment_20261107/clean_room_install*.log`。

最终实际执行的统一入口命令为（镜像继承本轮环境已记录的 USTC 配置）：

```bash
python3 scripts/deployment/validate_clean.py \
  --directory /home/wjz/peach_robot/clean_room_20261107 \
  --resume --stage all --jobs 2 --web-e2e --grasp
```

这是从本轮空环境起点继续处理安装问题，没有导入宿主机已安装的依赖或编译结果。
需要独立重现整个首次安装时，应使用新的目录名称，而不是 `--resume`。

## 阶段结果

| 检查 | 当前结论 | 判定依据 |
|---|---|---|
| 官方镜像 SHA-256 | 已通过 | 固定镜像哈希与官方 SHA256SUMS 一致 |
| 空环境起点 | 已通过 | ROS/Node/colcon/venv/build/install/旧前缀均不存在 |
| 系统依赖安装 | 已通过 | bootstrap 退出 0，主链 rosdep check 满足，厂商/规划器漏项已显式安装，Node 官方校验通过 |
| Python 固定版本与 pip check | 已通过 | 35 项实际版本匹配，导入通过，numpy 1.26.4，torch 2.13.0+cpu，pip check 无冲突 |
| npm 锁定安装与网页构建 | 已通过 | npm ci、SDK 类型检查、两组资源生成 |
| 全新 ROS 构建 | 已通过 | 45/45 包，最终构建日志退出 0；过程中的失败与续跑分别保留 |
| 只读 mock/HTTP/ROSbridge | 已通过 | GenericSystem、3 控制器、4 生命周期、PlanningScene 服务、数据流、六路 HTTP 与双帧 WS 投影正常，使能全关 |
| 浏览器检查 | 已通过 HTTP fixture 口径 | 五页、320/390/768/1440 四屏宽，28 passed / 0 failed；补字体后的截图已人工复核，中文可读；原生 WS 网页抓取未在此套件验收 |
| 单果 L6 mock 干跑 | 已通过单果口径 | request=deploy_acd92bb0b3f3；target_1 达 L6，工具关闭、回放暂停，wrapper 退出 0 |
| 录包与进程清理 | 已通过 | 最终两份 bag 为 14868/9848 条，流式读回与 metadata 一致；含失败轮在内共四份 bag 均完整可读；自有进程无残留 |

脚本参数错误返回 2、已有环境不带 `--resume` 时拒绝覆盖，已实际检查。
Python 脚本第一轮 flake8 发现格式和导入顺序问题，已修正；两份脚本的 flake8、pep257 均返回 0。
证据为 `runs/analysis_reports/deployment_20261107/deployment_scripts_flake8.log` 和
`deployment_scripts_pep257.log`。Shell 语法与 Node.js 语法检查通过。
阶段日志改为带时间和唯一标识的文件，并保留阶段历史；续跑会校验目录所有权标记。

## 最终结果与证据

`clean_room.json` 的 `full_validation_passed=true`。本轮从 Ubuntu Base 空白文件系统出发，
过程中修正依赖并显式续跑；后续构建可以继续使用本轮产生的中间文件，初始起点没有导入宿主机编译产物或依赖环境。
所有补包、版本固定和就绪检查都已写入最终脚本，源码与隔离工作区中的脚本哈希一致。

最终验证目录：
`/home/wjz/peach_robot/clean_room_20261107/workspace/runs/clean_validation/verification_20261106T184137Z`。

- [机器可读汇总](../runs/analysis_reports/deployment_20261107/clean_room_summary.json)。
- [完整验证 JSON](/home/wjz/peach_robot/clean_room_20261107/workspace/runs/clean_validation/verification_20261106T184137Z/verification.json)。
- [浏览器报告](/home/wjz/peach_robot/clean_room_20261107/workspace/runs/clean_validation/verification_20261106T184137Z/readonly_mock/web_e2e/report.json)。
- [修复字体前截图](/home/wjz/peach_robot/clean_room_20261107/workspace/runs/clean_validation/verification/readonly_mock/web_e2e/monitor_1440.png)、[最终截图](/home/wjz/peach_robot/clean_room_20261107/workspace/runs/clean_validation/verification_20261106T184137Z/readonly_mock/web_e2e/monitor_1440.png)。
- [所有轮次录包读回](../runs/analysis_reports/deployment_20261107/clean_room_all_bag_reads.json)。
- [宿主机最终进程/端口盘点](../runs/analysis_reports/deployment_20261107/clean_room_final_process_audit.json)。

单果结果与批次结果分开判定：target_2 因 `bag_axis_envelope_ill_conditioned` 被拒绝，
target_1 完成接近、套入、撤退并达到 L6。夹具在首颗成功后主动取消，
Action 为 `CANCELED`、`result.success=false`，同时单果 succeeded=1、wrapper exit=0；
不能解释成全部目标成功或真实剪切。

六类命名空间（user/mount/PID/IPC/network/UTS）均与宿主机不同，运行网络仅有 `lo`。
验收结束时宿主机没有 ROS 栈残留，8090/9090 均未监听。当时对原交付 2365 个既有 src 文件的逐文件核对显示内容未变，
驱动/控制器源码没有为通过检查而修改。

新建另一个目录从零复现的命令：

```bash
python3 scripts/deployment/validate_clean.py \
  --directory ../clean_room_reproduce \
  --ubuntu-mirror https://mirrors.ustc.edu.cn/ubuntu \
  --ros-mirror https://mirrors.ustc.edu.cn/ros2/ubuntu \
  --jobs 2 --web-e2e --grasp
```

## 证据入口与验收边界

过程元数据：[clean_room.json](/home/wjz/peach_robot/clean_room_20261107/clean_room.json)。
自动同步的阶段文档：[process.md](/home/wjz/peach_robot/clean_room_20261107/process.md)。
详细使用方式见 [部署说明](../scripts/deployment/README.md)。最终结果已与本轮
`verification.json`、编译日志、新请求账本和录包对应，历史失败证据单独保留。

官方 lint 与部署功能验证分别报告，上一轮只读驱动的 7 项 lint 失败和 cppcheck 跳过不会被抹去。
旧 IVG dashboard、Gazebo、真实硬件/SetIO/剪切及长期稳定性不属于本轮零环境 mock 验收结论。

## 验收后的文档同步

2026-11-07 随后更新根 README、打包恢复、文档索引、部署说明、系统测试/bringup/Web/SDK 入口，
修正手工依赖安装遗漏、GPU 必需的旧表述、历史绝对路径和精简交付未附带的归档链接。
冻结入口显式指定最小 bag 与 index 0，普通 bag 时钟和冻结重发时钟分别说明。
网页 HTTP fixture、只读 WS 投影和 CLI 单果干跑分别记录；使能、默认域和退出后停栈行为保持与脚本一致。

此轮只改文档，未重新启动 ROS 或宣称新增功能验收；原零环境、功能 JSON、失败日志与原部署工具包保持原状。
文档变更前备份、差异、链接/命令核对及非文档文件哈希审计保留在
`runs/analysis_reports/deployment_20261107/documentation_update_20261107T030039/`。
修订工具包为 `peach-deployment-kit-20261107-docs-v2.tar.gz`，附文件哈希清单及独立 SHA-256；
部署代码与固定依赖沿用已验证版本，补充包不包含完整源码、模型、录包和本机运行证据。
文档源码后来发生的修改不改变上述验收时 2365 文件一致性记录的历史含义。
