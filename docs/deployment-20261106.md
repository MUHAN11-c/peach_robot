# 2026-11-06 项目交付与部署

> 本页是 2026-11-06 历史交付记录，保留当轮依赖版本、手工命令和验收范围。当前部署请使用[部署脚本说明](../scripts/deployment/README.md)与[打包恢复入口](../README_PACKAGE.md)；新增依赖、35 项版本核对及独立 Ubuntu Base 的 2026-11-07 验收见[过程记录](deployment-validation-20261107.md)。本页的 34 项依赖结果不代表当前 requirements.txt。

本次交付按用户要求保留源码、必要模型/资产、配置/标定、文档及一份最小回放数据，省去可重新生成的编译产物、环境、前端依赖和缓存。本轮已经完成 45 个 ROS 包的完整编译、新路径全新编译、默认关闭使能的 mock 检查，以及一次单果 L6 冻结干跑。

**当前不能保证所有历史入口都能运行。** 旧 IVG dashboard 缺少已移出的 ros_web_link 和共享 JS；驱动/dashboard 按 AGENTS.md 保持只读、不启动。Gazebo 仍暂停；真实运动、SetIO、相机/串口硬件与真实剪切不在本次运行验收范围内。具体缺项在末节列明。

## 1. 包内容与空间

仅包含 src 源码、现行文档、必要 models/weights、标定配置、辅助工具源文件、一份约 9 MB 的真实 RGB-D/点云与 npz 样例，以及本轮简要验收证据。按用户最新要求不包含历史录包、历史归档、Git 历史、旧报告和设计副本。原工作区中的历史文件不删除。

不包含 build/install/log、aubo_py3.12、node_modules、Python/IDE/AI 缓存、IntelliSense 数据库、可再生前端 dist 和已确认可重渲输出。归档外的包含/排除清单记录本次实际范围。前端不可重取的 vendor 发行文件与当前感知模型保留。

这是项目源码和数据包，不是系统镜像。新机器需 Ubuntu 24.04 x86_64、ROS 2 Jazzy、Python 3.12、Node.js 22+。建议至少准备 20 GB 可用空间用于解压、重建依赖和编译；以本次交付校验记录的实际体积为准。

## 2. 校验和解压

桌面提供 tar.zst、同名 sha256、内容清单和交付校验记录。实际大小、SHA-256、压缩流及内容比对结果以后者为准。

```bash
cd /保存压缩包的目录
sha256sum -c aubo_e5_jazzy_ws-精简交付-20261106*.tar.zst.sha256
zstd -t aubo_e5_jazzy_ws-精简交付-20261106*.tar.zst
mkdir -p /新的恢复目录
tar -I zstd -xf aubo_e5_jazzy_ws-精简交付-20261106*.tar.zst -C /新的恢复目录
cd /新的恢复目录/aubo_e5_jazzy_ws
```

当前目录中应只有一份匹配本次名称的包。解压到新目录，避免覆盖正在使用的工作区。先阅读根 AGENTS.md。

## 3. 安装系统依赖

先按 Jazzy 官方方式安装 ROS 2。下面命令在目标机执行，需要管理员权限与可用软件源；本次没有更改系统 apt 安装。

```bash
source /opt/ros/jazzy/setup.bash
sudo apt install python3-venv python3-colcon-common-extensions python3-colcon-python-setup-py \
  python3-rosdep nlohmann-json3-dev zstd
# 仅在尚未初始化 rosdep 时由管理员执行一次 sudo rosdep init
rosdep update --rosdistro jazzy
sudo apt install ros-jazzy-camera-calibration ros-jazzy-web-video-server
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y \
  --skip-keys "ament_python nlohmann_json ros_web_link"
```

原始 rosdep 检查有三个未解析键：ament_python、nlohmann_json、旧 ros_web_link。前两项通过上面的显式工具/库安装满足；跳过 ros_web_link 不会修复旧 IVG 面板，当前不能启动该面板的旧组合入口。本机还缺上面两个可选 apt 包，本轮 mock 不使用它们。系统版本清单在 runs/analysis_reports/delivery_20261106/apt_packages.tsv。

## 4. 重建 Python 环境

ROS Python 包来自 Jazzy apt，不能用 pip 覆盖。Python 3.12 venv 使用系统 site-packages；numpy 固定 1.26.4，不能升至 2.x。

```bash
python3 -m venv --system-site-packages aubo_py3.12
aubo_py3.12/bin/python -m pip install -r requirements.txt
# IVG 可选抠图能力：禁止 rembg 自动升级 numpy
aubo_py3.12/bin/python -m pip install --no-deps rembg==2.0.61
# 避免 Ubuntu 旧 matplotlib 的 namespace 抢占新版本 mplot3d
cp scripts/deployment/peach-matplotlib-nspkg.pth \
  aubo_py3.12/lib/python3.12/site-packages/peach-matplotlib-nspkg.pth
```

requirements 中 34 项固定版本均与本轮已运行环境一致；完整 Python 版本快照为 python_freeze.txt。关键包的 Python 源文件已核对安装 RECORD，无内容修改。包管理器下载仍需可用软件源；本轮验证复用了匹配版本依赖，没有宣称在全新系统上重新下载并安装全部依赖已实测。

## 5. 重建网页和全部 ROS 包

必须先安装前端锁定依赖；只有源码时 CMake 可以编译通过但不会生成缺失的 Web dist，不能遗漏 npm ci。

```bash
node --version  # 要求 22+
npm --prefix src/ros2_web_link ci
npm --prefix src/ros2_web_link run check
npm --prefix src/ros2_web_link run build
npm --prefix src/peach/peach_web ci
npm --prefix src/peach/peach_web run build:vendor
source /opt/ros/jazzy/setup.bash
export CMAKE_BUILD_PARALLEL_LEVEL=2
export MAKEFLAGS=-j2
colcon --log-base log/restored_build build \
  --base-paths src --build-base build_restored --install-base install_restored \
  --executor parallel --parallel-workers 2 \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

使用新终端，不预先加载其它工作区。迁移时不要复制旧 CMake 缓存，也不要 source 被移除包的旧 install。本轮在 /tmp/peach_delivery_relocate/ 的全新 build/install 中构建 45/45 包通过；已核对安装索引与导入模块来自新路径。纯资源包关于 CMAKE_EXPORT_COMPILE_COMMANDS 未使用的提示不属于编译失败。

## 6. 加载运行环境

从恢复后的工作区根执行，先 ROS，再新 install，再 venv：

```bash
source /opt/ros/jazzy/setup.bash
source install_restored/setup.bash
source aubo_py3.12/bin/activate
export PYTHONPATH="$PWD/aubo_py3.12/lib/python3.12/site-packages:${PYTHONPATH:-}"
export ROS_LOG_DIR="$PWD/log/restored_runtime"
export MPLCONFIGDIR="$PWD/.cache/matplotlib"
export YOLO_CONFIG_DIR="$PWD/.cache/ultralytics"
python3 -c 'import sys,numpy,cv_bridge,open3d; print(sys.executable,numpy.__version__,cv_bridge.__file__,open3d.__version__); assert numpy.__version__ == "1.26.4"'
```

## 7. 直接运行随包数据

[数据说明](../runs/data/delivery_simulation_20261106/README.md)包含来源、哈希和全部命令。样例有真实同步 RGB/深度/两路内参/点云，以及 8 个真实 npz 输入；不携带原始 60 秒 bag，只携带从中无修改提取的同步帧；来源路径用于追溯。

先盘点已有进程，确认 DDS 域 181、HTTP 8090 与 WS 9090 空闲，不覆盖其它任务：

```bash
export ROS_DOMAIN_ID=181 ROS_LOCALHOST_ONLY=1
export AUBO_RUNS_DIR="$PWD/runs/data/restored_replay"
ros2 launch peach_system_tests frozen_camera_grasp.launch.py \
  bag:="$PWD/runs/data/delivery_simulation_20261106/rgbd_frame_bag" \
  frame_index:=0 hz:=2 rviz:=false
```

该入口不发抓取请求，execution/grasp/tool 均 false，autostart=false。浏览器打开 http://127.0.0.1:8090。不要直接对零时长单帧包使用 bag play --loop；使用上面的冻结发布器。退出用 Ctrl+C，等待录包封口，并按 testing.md 只清理本轮进程。

需验证一次 mock 完整干跑时，先退出上述栈，再按数据说明运行 run_frozen_grasp.py --bag … --index 0。该驱动会先核验 GenericSystem，再显式开启 mock 执行/接触；tool 始终关闭。本轮 wrapper 退出 0，target_1 达到 L6，回放暂停、自有组无残留；另一个目标因 bag_axis_envelope_ill_conditioned 被拒绝。夹具在首颗成功后主动取消批次，所以 Action CANCELED/result.success=false 不等于所有目标成功，也不证明真实剪切。

## 8. 本次验证记录与已知限制

证据目录为 runs/analysis_reports/delivery_20261106/：

- 原路径完整构建 45/45，新路径全新构建 45/45；最初旧缓存路径错误与修复后日志均保留。
- 接口清单 62 active + 5 reserved 通过；Web SDK 类型检查通过。
- 离线感知实际运行 3 帧（1 预热、2 稳态），稳态每帧 5 个检测、4 个候选；单次短样本不作为性能上限。
- 原路径及新路径的只读 mock 均通过：4 个生命周期节点 active、3 个控制器 active、关节序与唯一发布者正确、三路回放数据持续发布、六个 HTTP 路径为 200；全部使能关闭，退出无自有残留。
- 冻结干跑修正了有限驱动成功退出被误报为提前退出的问题。独立复现确认：声明完成的 0 正常、长驻进程提前 0 仍报错、驱动非零仍报错。未在 test/ 新增行为套件。
- 样例 bag 的 5 条消息与成功会话 bag 的 10535 条消息均完整流式读回，数量与 metadata 一致；Matplotlib 3D 实际绘图通过。
- 本轮独立结果目录：43 包完成、121 项检查、0 errors、7 failures、0 skipped。7 项全部属于按规定只读的 4 个驱动包：aubo_dashboard copyright/cpplint；aubo_e5_bringup copyright；aubo_e5_controllers cpplint/uncrustify；aubo_e5_hardware copyright/cpplint。没有修改驱动掩盖失败。
- aubo_ros2_web_dashboard、ivg_sim 没有测试，首次执行因无测试返回 5，随后明确排除。初次 test-result 的 2538 项混入历史缓存，不代表本轮；以 fresh_test_results.log 的 121 项为准。
- XML lint 的网络失败已用官方 ROS schema 离线副本解决，规则未放宽；来源与用法见 schemas/README.md。
- rosdep 未解析键、两个可选 apt 缺项，以及旧 IVG 面板缺口均保留原始记录。真实硬件、SetIO/剪切、Gazebo 和旧面板没有运行验收。

Gazebo 的大体积 field_no_grass.glb 与重渲输出未携带；源码和小型资产保留，重建方法见 sim_worlds/README.md。当前约束仍暂停 Gazebo；随包可直接运行的是已验证的 mock/冻结回放。

现行文档入口：根 README.md，docs/README.md、docs/architecture/，各包 README 与 doc/architecture.md、doc/io.md，接口权威清单 peach_interfaces/config/interface_manifest.yaml，测试指导 peach_system_tests/doc/testing.md，Web 手册 peach_web/doc/debug-testing.md。实际 45 个包均有 README。历史快照不代替当前源码和文档。
