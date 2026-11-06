# sim_worlds 架构

2026-11-06 源码快照。场景数据和生成在本包，机器人模型/控制器在 `sim_description`，组合在 `sim_bringup`，导航/持果/放筐任务在 `sim_harvest`。Gazebo 当前暂停，本次仅做文档与静态核对。

## 单一资源链

```text
config/orchard.yaml → params → scene / nav_map → 程序化 SDF + manifest + map

历史 Blender v11 → blender/export_data_orchard.py
                 → worlds/data_orchard/assets.json + GLB
                 → data_orchard.prepare_data_orchard(runtime/scene)
                 → SDF + manifest + map + tree survey stations

demo.prepare_demo(runtime/scene) → 轻量世界 + manifest + map + stations

历史整园 GLB/scene_manifest → field_gt → field_map + field_stations（预览）
```

联合 `sim_bringup/harvest.launch.py` 根据 `scene` 只选择一套同源资源，再把生成路径传给 Gazebo、Nav2 和 sim_harvest。`field` 没有目标 manifest，不能按整园网格执行逐果采收。场景内 robot 的 URDF 名、Gazebo 实体名和目标 ID 属于不同身份，不能互换。

## 模块职责

| 模块 | 职责 |
|---|---|
| `params.py` | typed 参数、YAML 转换及几何/范围检查 |
| `scene.py`、`textures.py` | 程序化果园、工具/目标几何描述与贴图 |
| `nav_map.py` | 与程序化布局同源的占据栅格 |
| `cli.py` | generate_orchard 文件边界；`--check` 不写文件 |
| `demo.py`、`mesh_geometry.py` | 小世界、刚性袋果代理、SDF 与工具可视尺寸 |
| `data_orchard.py` | 校验源网格哈希/路径，生成同源视觉、碰撞、地图与观察站位 |
| `field_gt.py` | 历史整园清单的地图/站位生成 |
| `preview.py`、`tour_core.py`、`tour_node.py` | 离线预览、站位计算及独立 Nav2 巡游 |
| `xmlsafe.py` | 场景 XML 边界辅助 |

本包不产出 Peach 感知候选，不实现 BuildTargetModel，也不读取真实柜侧状态或发 SetIO。仿真视觉模式的候选来自共享 Peach RGB-D 能力；实体真值只在仿真执行边界关联，不能作为视觉位姿成功证据。

模块职责不表示资源格式可以互换：旧 orchard_manifest/v1 保存程序化目标与平台，但 _manifest 当前不写 obstacles；Grasp 默认只补地面及目标盒，不能自动得到世界中的全部树干/枝条。data_orchard/v1 则显式提供 woody obstacles。field_stations 的 x/y/yaw 格式与 demo/data_orchard 的 id/nav_pose 任务格式也不同，只供对应预览/兼容路径消费。完整文件接口见 [io.md](io.md)。

## 数据驱动小果园

`assets.json` 记录源 blend、先验/审计、导出器与每个网格 SHA-256。运行生成时拒绝目录逃逸或哈希变更，再把视觉网格路径、目标尺寸/袋底/轴、质量假设与碰撞包络写进当前 manifest。树级 survey 站位不编码“应该选哪颗果”。

枝干碰撞使用实际网格环提取的圆柱段；导航地图仅投影底盘/激光高度带内的木质几何，上层树冠仍是臂侧三维障碍。叶片视觉减面不等于删去枝干或袋果碰撞。袋果是刚性代理，不仿真柔性袋、真实刀刃力或摩擦持有。数据来源和限制见 [SOURCE](../worlds/data_orchard/SOURCE.md)。

## 文件与运行边界

- `setup.py` 安装 Python 包、config、worlds、textures、data_orchard 与 maps；开发期 Blender/重建脚本不随节点自动运行。
- 运行时世界/地图/站位写到 `peach_sim/.runtime/`，不改源资源；显式离线重导出也使用新目录。
- `build/`、`install/`、`log/` 由子工作区运行器管理，使用独立 ROS domain 与 GZ partition。根工作区驱动/模型只读引用。
- BUNKER 模型来源已归属 [sim_description/meshes](../../sim_description/meshes/BUNKER_SOURCE.md)，不再引用本包不存在的 meshes 路径。

## 核对与历史兼容

包内 `test/` 只有官方 ament lint。旧版“sim五包行为测试/launch_test”与过滤不存在用例的命令不再代表现状；六包联合仿真的运行验收须在用户恢复 Gazebo 后进行，不能由 lint 或离线图像补成通过。

`reconstruction/` 中仍有离线探针引用旧 `peach_harvester/model/`；它们不在现行 launch 或包 console scripts 链，保留用于历史重现，运行前须核模型路径及配置。旧手册与未安装的 sim_perception 视觉副本已归档，不能作为当前第二套运行实现。

离线开发目录还有 Blender unittest 检查器与数据/渲染门，但不由 setup 安装、不被 package/test 收集，不能与 colcon 官方 lint 混写。各脚本的输入、输出、副作用和历史绝对路径见 [offline-tools.md](offline-tools.md)。
