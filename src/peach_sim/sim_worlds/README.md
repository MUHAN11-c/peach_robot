# sim_worlds

独立仿真子工作区的场景资源与离线生成工具。当前联合入口默认 `data_orchard`，也支持 `demo`、`orchard` 和 `field`；机器人模型在 `sim_description`，系统组合在 `sim_bringup`，任务/持果/入筐在 `sim_harvest`。

**Gazebo 当前暂停。** 本页按 2026-11-06 源码整理，命令与资产说明不代表导航、视觉采收或入筐已经通过。运行授权与统一入口见 [peach_sim README](../README.md)。

## 当前场景

| scene | 资源与用途 |
|---|---|
| `data_orchard` | `worlds/data_orchard/assets.json` 与导出网格；两株树、35 颗独立袋果、3615 段枝干碰撞，由同一清单生成世界、manifest、地图和树级观察站位 |
| `demo` | `sim_worlds/demo.py::prepare_demo` 生成轻量确定性世界、目标和站位；真值任务的有限验证环境 |
| `orchard` | `config/orchard.yaml` 经 `params.py` / `scene.py` / `nav_map.py` 生成程序化果园、目标清单与地图 |
| `field` | 历史整园 GLB 和 `maps/field_*` 用于导航/视觉预览；无独立袋果实体，联合 launch 不创建采摘任务，不使用 `--mission` |

`data_orchard` 保留原袋果的大小、倾角、遮挡和来源，没有按工具可容纳程度筛选。网格哈希、重导出方式、数据估计与推断布局的区别见 [SOURCE.md](worlds/data_orchard/SOURCE.md)。离线渲染检测不能证明 Gazebo 相机闭环。

## 源码与安装

现行 console scripts 由 `setup.py` 声明：

- `generate_orchard`：`sim_worlds.cli`，读参数、校验布局，输出 SDF/manifest/贴图，可选地图。
- `generate_field`：`sim_worlds.field_gt`，从历史重建清单生成整园地图与站位。
- `scene_preview`：`sim_worlds.preview`，离线场景预览。
- `orchard_tour`：`sim_worlds.tour_node`，基于站位的 Nav2 巡游工具，非当前默认任务编排器。

`prepare_demo` / `prepare_data_orchard` 是联合 launch 调用的生成函数，不是额外 console scripts。`setup.py` 安装 Python 包、配置、worlds（含 data_orchard/贴图）及 maps；`blender/` 和 `reconstruction/` 是源码开发工具，不由节点自动运行。

## 构建、核对与输出

从 `peach_sim/` 使用 `scripts/sim`，构建/安装/日志/用户缓存都留在子工作区。不要用旧手册里的工作区根构建或绕过运行器启动 Gazebo。离线参数检查可使用：

```bash
scripts/sim check python3 -m sim_worlds.cli --check
```

显式生成场景时将 `--out-dir` 指向新的 `.runtime/` 子目录；`--map` 将 maps 写到该输出目录的同级。默认 CLI 输出指向包 share，重现时应显式指定新目录以保留原资产和历史证据。

自动检查为官方 ament flake8/pep257，不能替代场景碰撞、相机成像、导航和采摘运行验收。恢复运行后仍须独立 domain/partition、有界会话和精确进程组收尾。

## 模型与历史材料

机器人、三种真实工具的只读装配及 BUNKER 外观资产在 [sim_description](../sim_description/README.md)；来源见 [BUNKER_SOURCE.md](../sim_description/meshes/BUNKER_SOURCE.md)。本包不维护另一套机器人或真实驱动。

`reconstruction/` 保留历史 Blender 重建、先验、渲染和比较工具；`blender/export_data_orchard.py` 仍用于当前资产重导出，不能整目录当成冗余删除。部分旧感知评估脚本仍将模型路径写为已退役的 `peach_harvester/model/`，不属于当前 launch 链，直接使用前须修订到 `peach_scene_perception/model/` 并重新验证，旧结果不作当前默认模型验收。

改写前的旧手册已保存在工作区 `_archive/source_docs_2026-11-06/`，原路径与 SHA-256 可查。结构和数据流见 [architecture.md](doc/architecture.md)。

四个 console scripts、生成函数的实际参数/产物和不同 manifest 版本见 [接口](doc/io.md)；Blender、重建、渲染、评估脚本的逐组索引及历史路径限制见 [离线工具](doc/offline-tools.md)。旧 orchard manifest 当前不含枝干 obstacles 列表，不应套用 data_orchard 的规划障碍完整性说明。
