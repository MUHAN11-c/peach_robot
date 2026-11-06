# 工作区打包与恢复

GitHub 用户可直接克隆本仓库，或在 [v1.0.0 Release](https://github.com/MUHAN11-c/peach_robot/releases/tag/v1.0.0)
下载完整包及校验文件；仓库已携带必需模型、最小 bag 和精选验收证据。下面的本机路径属于原发布过程记录，
跨机器使用时按当前解压/克隆目录执行，不依赖原宿主目录。

## v1.0.0 完整稳定交付

当前交付使用 `peach_robot-v1.0.0.tar.zst`，发布目录为本项目上级的 `releases/v1.0.0/`。
包内包含完整源码、Peach 模型、最小回放与部署脚本，直接解压重建；旧工具包不再是恢复前提。
发布范围、已知限制和实际验收依据见[版本说明](docs/releases/v1.0.0.md)。

```bash
sha256sum -c peach_robot-v1.0.0.tar.zst.sha256
tar --zstd -xf peach_robot-v1.0.0.tar.zst
cd peach_robot-v1.0.0
python3 scripts/package_release.py --check ../peach_robot-v1.0.0.tar.zst
bash scripts/deployment/deploy.sh --system --verify --jobs 2
```

稳定打包使用 `python3 scripts/package_release.py --output ../releases/v1.0.0`，始终包含夹具和精选证据，
生成逐文件清单并完整读回压缩包；已有发布目录拒绝覆盖。发布包解压后的额外复查结果见同目录 `ACCEPTANCE.json`。
下文保留普通源码迁移方式与早期交付背景；普通打包脚本默认不含运行数据，与稳定完整包的范围不同。

部署说明更新至 2026-11-07。新机器恢复使用[部署脚本](scripts/deployment/README.md)，
从空白 Ubuntu 开始的安装问题、修正和实际结果见[过程记录](docs/deployment-validation-20261107.md)。
本轮 45 包构建、35 项 Python 固定版本、HTTP 网页 28 项与单果 L6 均有独立根文件系统证据；
不代表真实硬件、原生 WS 网页抓取或长期稳定性已通过。

## 当前部署与历史交付

2026-11-07 本机部署位于 `/home/wjz/peach_robot/aubo_e5_jazzy_ws`。使用纯英文路径，
含中文的交付目录在当前 Jazzy rosidl/CMake 接口生成阶段会失败。原始压缩包、清单与旧工具包集中保留在项目上级 `archives/`；重复解压目录在核对原包完整性和差异后删除。
本机缺少免密 sudo，宿主机早一轮部署将额外 Jazzy apt 包解压至 `.deps/root`，没有写入系统目录；
该目录由下面的环境入口加载，宿主机 `rosdep check` 仍会将这些包列为未安装。
随后新建的 `clean_room_20261107` 则在自己的根文件系统内经 apt/pip/npm 安装依赖，未导入此宿主机前缀。

```bash
cd /home/wjz/peach_robot/aubo_e5_jazzy_ws
source scripts/deployment/env.bash
ros2 launch peach_bringup harvest_system.launch.py hardware_mode:=mock \
  camera_enabled:=false force_enabled:=false rviz:=false autostart:=false
```

环境入口同时关闭用户级 Python 包加载，使用本目录的 install、venv 和本地 apt 前缀。
当前主机没有可用 NVIDIA 设备，PyTorch/TorchVision 使用对应锁定版本的 CPU 发行轮子。
全新 pip 安装发现 PyMatting 1.1.15 与旧 Numba 固定版本冲突；已将 Numba/llvmlite
修正为 0.60.0/0.43.0，NumPy 仍为 1.26.4，兼容依据见 requirements.txt 的官方链接。
Matplotlib 的 namespace 辅助文件在本地绘图库尚未安装时现在会安全跳过。
当前固定清单共 35 项，包含 setuptools 78.1.0；零环境内 `pip check` 无冲突。
本轮原始日志和结果位于 `runs/analysis_reports/deployment_20261107/`，不沿用交付包中的历史测试结果。

2026-11-06 原始精简交付的实测结果、可用回放数据与当时限制保留于
[历史交付说明](docs/deployment-20261106.md)。该次交付省去可重新生成的编译产物、环境和缓存，保留源码、必要模型、一份最小回放数据、文档与当轮验证记录；不携带历史录包、归档和 Git 历史。历史依赖版本与手工恢复命令不替代下述当前入口。

本页说明当前 [pack_workspace.sh](scripts/pack_workspace.sh) 的行为。生成物的实际版本、时间和可选内容应随该次交付单独记录。2026-10-23 迁移包原说明仅存于原工作区 `_archive/`，本精简交付未附带。

## 包含范围

默认包含当前存在的 `src/` 源码与资产、`docs/`、`wiki/` 导航、`reports/`、`weights/`、`peach_autonomous_harvest_design/`、根文档、`scripts/`、`requirements.txt`、构建配置、`.github`、`.agents`、规则和 `.git/` 历史。`--no-git` 取消历史。

- `--include-archive`：附带 `_archive/` 历史原件；默认不含。
- `--include-tools`：附带 `_tools/`，包含 Blender、cadenv 等本机工具；默认不含。
- `--records-days N`：附带 `runs/` 最近 N 天内修改过的完整顶层会话，包括对应 bag/截图；默认不含运行证据。

脚本保留前端 vendor 发行文件及当前感知模型 `src/peach/peach_scene_perception/model/`。colcon 的任意层级 `build/`、`install/`、`log/`、venv、node_modules、工具缓存和可重下/重渲大件按脚本排除；前端 vendor 的 `build/` 发行目录有专门保留规则。`reconstruction/output/` 按 Git 索引区分已跟踪交付件与未跟踪生成物。此精简目录没有 Git 历史，不能据它重现原仓库的跟踪清单；重新交付应核对 dry-run、实际文件与回放夹具是否齐全。

## 预览与生成

在工作区根运行：

```bash
scripts/pack_workspace.sh --dry-run --out /tmp
scripts/pack_workspace.sh
# 示例：附带归档、工具和最近两天的整条证据
scripts/pack_workspace.sh --include-archive --include-tools --records-days 2
```

默认输出在工作区上一级，文件名含实际打包时间。`--out DIR` 改目录，`--zstd` / `--gz` 指定压缩格式；`--help` 查看完整选项。先检查磁盘空间和 dry-run 的包含/排除范围。

## 目标环境恢复

将源码解压到无空格的英文路径后，在工作区根执行。`--system` 安装 Ubuntu/Jazzy/Node 依赖，需要 root/sudo；脚本同时处理已知 rosdep 映射和厂商 manifest 漏项：

```bash
bash scripts/deployment/deploy.sh --system --verify --jobs 2
# 部署检查会自动停栈；常驻 mock 另加载环境后启动。
source scripts/deployment/env.bash
```

若恢复 2026-11-06 历史原始源码交付，可从项目上级 `archives/deployment-kits/` 取 `peach-deployment-kit-20261107-docs-v2.tar.gz` 覆盖解压到旧工作区；该补充包没有完整源码、模型或录包。v1.0.0 已整合这些修正，无需此步骤。

验证需要 `runs/data/delivery_simulation_20261106/rgbd_frame_bag/metadata.yaml` 及其存储文件。通用打包默认不含 `runs/`，所以不能只复制源码后把缺夹具当作功能失败或跳过通过。`--verify` 保持使能关闭；可另追加 `--web-e2e --grasp`，后者显式执行工具关闭的 mock 单果干跑。

宿主机没有 ROS 或 sudo 时，可在新目录创建 Ubuntu Base 验证环境；宿主需 Python 3、curl、tar、bubblewrap 和可用的用户命名空间：

```bash
python3 scripts/deployment/validate_clean.py --directory ../clean_room_trial \
  --ubuntu-mirror https://mirrors.ustc.edu.cn/ubuntu \
  --ros-mirror https://mirrors.ustc.edu.cn/ros2/ubuntu \
  --jobs 2 --web-e2e --grasp
```

安装阶段联网，运行阶段只启用独立网络的回环接口。`--resume` 用于本轮失败后续跑，只同步部署脚本与依赖；应用源码变更后创建新目录。阶段日志、`clean_room.json` 与自动生成的 `process.md` 均保留。环境共享宿主内核；不要在宿主直接 source 环境内 `/workspace` 安装产物。`src/peach_sim` 仍采用独立子工作区，Gazebo 保持暂停。

可重下资产入口：IVG 权重见 [models/README.md](src/ivg/ivg_pose_estimation/models/README.md)，YCB meshes 见 `src/ivg/ivg_sim/models/fetch_ycb.sh`；仿真重建资产见 [sim_worlds](src/peach_sim/sim_worlds/README.md)。

## 压缩包校验

```bash
zstd -t aubo_e5_jazzy_ws-src-*.tar.zst
tar -tf aubo_e5_jazzy_ws-src-*.tar.zst | head
```

核对交付版本、配置、模型及所需证据后再按 [测试指导](src/peach/peach_system_tests/doc/testing.md) 启动 mock。硬件运行仍遵循 [AGENTS.md](AGENTS.md) 的授权与进程清理约束。
