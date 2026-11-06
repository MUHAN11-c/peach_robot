# 部署与零环境验证

目标系统为 Ubuntu 24.04 amd64、ROS 2 Jazzy、Python 3.12、Node 24.18.0。
部署路径使用无空格的英文路径。驱动和控制器源码保持只读；这些脚本只运行 mock。
说明同步日期：2026-11-07；功能结果对应当日 02:44（Asia/Shanghai）完成的零环境验收。
需完整源码、感知模型和 `runs/data/delivery_simulation_20261106/rgbd_frame_bag/` 最小夹具，
其中须保留 `metadata.yaml` 及存储文件；部署工具包本身不附带这些资产。

## 部署新机器

在源码工作区根目录执行：

```bash
bash scripts/deployment/deploy.sh --system --verify --jobs 2
```

`--system` 安装系统 apt 依赖、ROS 软件源与 Node，需要 root/sudo；已有这些依赖时省略。
脚本随后创建 `aubo_py3.12`，安装固定版本 Python 包和 PyTorch CPU 轮子，执行两个
`npm ci`、SDK 类型检查、网页资源生成、全部 ROS 包构建和接口清单检查。
Python 用户级包与已有工作区环境变量会在部署子进程中隔离。
setuptools 固定为 78.1.0，同时满足当前 Torch 和 Jazzy colcon 的版本约束。
`requirements.txt` 共 35 项；NumPy 1.26.4，Numba/llvmlite 0.60.0/0.43.0。
不会改写登录 shell 配置。

`--verify` 启动冻结 RGB-D 的只读 mock 栈，检查 GenericSystem、三路控制器、四个生命周期节点、
关节排列与动态状态值、图像/点云、`/get_planning_scene` 服务、六条 HTTP 路径和
ROSbridge allowlist 中的两帧 `web_state` 投影，所有执行/抓取/工具使能关闭。
退出后停止本轮进程并完整读回会话录包，不保留常驻 8090/9090 服务。

显式增加以下选项可扩大验证：

```bash
bash scripts/deployment/deploy.sh --verify --web-e2e --grasp --jobs 2
```

- `--web-e2e` 下载 Chromium，检查中文字体，运行 HTTP fixture 的五页和四种屏宽浏览器检查。
  套件会创建一次关闭执行的调试会话，不能称为纯只读；不包含原生 WS 网页抓取。
- `--grasp` 在确认 mock 硬件后显式执行单果完整干跑，工具关闭；驱动在首颗成功后取消批次。
  达到 L6 表示撤退已确认，不代表整批成功或真实剪切。
- `--output /绝对/新目录` 指定本次日志目录。默认位于 `runs/deployment/<UTC时间>/`。

独立复查已有部署，不重新安装或构建：

```bash
bash scripts/deployment/verify.sh --output runs/deployment/manual_verify --web-e2e --grasp
```

输出目录必须不存在，防止混入历史结果。测试需空闲的 DDS 域（默认 181）、8090/9090 端口。
脚本只清理自己创建的进程组，不清理其它任务。
启动常驻应用时先 `source scripts/deployment/env.bash`，再使用根 README 的 mock 命令。

## 从空白系统验证

宿主机只需要 Python 3、curl、tar 和 bubblewrap；无需 Docker、宿主机 ROS 或管理员权限。
Ubuntu 上 bubblewrap 的包名为 `bubblewrap`，需要内核允许用户命名空间。

```bash
python3 scripts/deployment/validate_clean.py \
  --directory ../clean_room_trial \
  --jobs 2 --web-e2e --grasp
```

国内网络可显式选择镜像；apt 仍验证 Ubuntu/ROS 软件包签名：

```bash
python3 scripts/deployment/validate_clean.py \
  --directory ../clean_room_trial \
  --ubuntu-mirror https://mirrors.ustc.edu.cn/ubuntu \
  --ros-mirror https://mirrors.ustc.edu.cn/ros2/ubuntu \
  --jobs 2 --web-e2e --grasp
```

验证器下载固定 SHA-256 的官方 Ubuntu Base 24.04.5 镜像，创建独立根文件系统、HOME、
PID/IPC/UTS/挂载命名空间，只复制源码、模型和最小回放数据。
初始检查拒绝存在 ROS、Node、colcon、build、install、venv 或旧 `.deps` 的环境。
宿主机系统目录、用户目录和包缓存不挂载到环境中。
只有单个 UID 映射时，fakeroot 仅用于 apt 包所有权元数据的模拟；依赖库仍从环境内的 apt/pip/npm 安装。

安装和构建阶段允许联网；运行验证阶段切换到仅有回环接口的独立网络，并检查该条件。
因此 mock 运行阶段没有通往真实相机或机器人的网络路径。该环境共享宿主机内核，属于根文件系统隔离验证。
首次安装 CA 证书通过 Ubuntu GPG 签名验证的 apt 完成，随后使用 HTTPS。

`clean_room.json` 记录基础镜像哈希、初始条件、命名空间、各阶段退出码和日志位置。
每个检查点自动同步生成 `process.md` 过程文档；阶段日志使用唯一文件名，历史失败日志不会被续跑覆盖。
部署日志位于隔离工作区的 `runs/clean_validation/deployment*/`，验证结果和录包位于
`runs/clean_validation/verification*/`；再次验证创建新的结果目录。路径中的 `/workspace` 是环境内路径，对应外部的
`<directory>/workspace/`，不应直接在宿主机 source 其 install。

调试安装中断时，可保留该环境并明确继续某一阶段：

```bash
python3 scripts/deployment/validate_clean.py --directory ../clean_room_trial \
  --resume --stage system
python3 scripts/deployment/validate_clean.py --directory ../clean_room_trial \
  --resume --stage build --web-e2e
python3 scripts/deployment/validate_clean.py --directory ../clean_room_trial \
  --resume --stage verify --web-e2e --grasp
```

`--resume` 只接受验证器创建并带所有权标记的目录；默认拒绝覆盖已有环境。
重做系统或构建阶段会使后续通过状态失效，历史证据仍保留，避免把旧验证结果当作新验收。
续跑只同步部署脚本与依赖清单；应用源码变更后应创建新的零环境。
需要新一轮从零验证时使用新的目录名。

本次执行中的发现、修正和证据汇总见
[2026-11-07 过程记录](../../docs/deployment-validation-20261107.md)。

## 范围与结果判定

本轮验收已完成 45/45 包构建、35 项 Python 固定版本匹配与 `pip check`、HTTP 浏览器 28/28、
只读 WS 状态投影和单果 L6。单果夹具的批次 Action 为 CANCELED、result.success=false，
单果 succeeded=1、wrapper exit=0；最终两份 bag 为 14868/9848 条且完整可读，自有进程无残留。
这些数字属于上述日期的证据，不是后续运行的预期替代值。

所有发现的 45 个包均构建；系统依赖按全部包的构建/测试依赖和当前 Peach 主链的运行依赖安装。
Gazebo 不启动，其可选运行时不列入该部署验收。旧 IVG 面板的 `ros_web_link` 仍属于已知缺口。
`ament_python` 与 `nlohmann_json` 的 rosdep 映射缺口分别由 colcon 工具和 `nlohmann-json3-dev` 满足。
厂商 Percipio 包的 package.xml 未列全 CMake 依赖，脚本额外显式安装 camera_info_manager、
image_transport、image_publisher、pcl_conversions、tf2_sensor_msgs；厂商源码保持原样。
MoveIt 启动配置使用的 Pilz 和 STOMP 规划器也显式安装，验证器检查插件索引及
`/get_planning_scene` 服务就绪。中文界面依赖 fonts-noto-cjk，验证前检查中文字体覆盖。
可选 IVG 抠图能力不在默认部署验收中。

部署脚本遇到任一安装、构建或功能验证失败都会返回非零并保留日志。
官方 lint 应独立运行并单独判定；此前全包检查仍有 7 项只读驱动 lint 检查失败，70 个 cppcheck 用例跳过。
本轮新部署脚本的 flake8/pep257 与 Shell/Node 语法通过，不据此认定全仓 lint 通过。
真实运动、SetIO、真实剪切和长期稳定性验收仍需相应现场测试。

参考：
[ROS Jazzy 安装源文档](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Installation/Ubuntu-Install-Debs.rst)、
[Ubuntu Base 与校验和](https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/)、
[bubblewrap](https://github.com/containers/bubblewrap)。
