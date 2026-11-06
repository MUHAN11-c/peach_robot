# sim_worlds 文件与工具接口

没有常驻场景生成节点或自定义 IDL。运行 world 消费 Gazebo 标准系统；本包唯一会向 Nav2 发动作的 console script 是独立 orchard_tour，不能把它当作当前 Mission 的操作租约/许可实现。Gazebo 当前暂停。

## 安装入口

- generate_orchard（cli.main）：--params 默认 share/config/orchard.yaml；--check 在参数和布局校验后退出、不写文件；--out-dir 默认 share/worlds，生成 peach_orchard.sdf、peach_orchard.manifest.yaml 和 textures。--map 另向 out-dir 同级 maps/ 写 orchard_map.pgm/yaml。保留源资产时必须显式指定新输出目录。
- generate_field（field_gt.main）：--manifest 必填，--out-dir 默认当前目录下 maps，--row-gap 默认0.9、--side=±1；输出 field_map.pgm/yaml 与 field_stations.yaml。它读取历史重建 connections/targets，不创建独立袋果实体或 Pickup manifest。
- scene_preview（preview.main）：--package-dir 默认模块包根，读取该目录 config/orchard.yaml 并现算程序化场景，再将简单几何/目标投影为 PNG；--out 默认 worlds/peach_orchard.preview.png。安装位置未必在该默认目录旁保留 config，调用方须核实并显式指向实际 share。它不是 Gazebo 截图，也不是 data_orchard 任意 GLB 的真实渲染器。
- orchard_tour（tour_node.main）：--params、--rows、--dwell、--timeout，使用 BasicNavigator、map 目标和 use_sim_time，逐站等待/停留；没有 Mission 的 Pick/Survey/模型许可/operation.lock 链。当前联合采摘使用 sim_harvest.run_harvest。

## 组合调用函数

prepare_demo(output_directory) 和 prepare_data_orchard(output_directory, asset_directory=None) 返回 world、manifest、map、stations、scene_params 的 Path 映射。两者创建输出目录并可覆盖同名生成文件，不在 API 内提供历史证据备份；调用方使用新的 runtime 子目录。

demo 生成 demo.sdf、demo.manifest.yaml、map.pgm/yaml、stations.yaml；data_orchard 从 assets.json 校验目录包含关系及每个网格 SHA256，保留袋尺寸/轴和碰撞段，生成 data_orchard.sdf、orchard.manifest.yaml、map.pgm/yaml、stations.yaml。data_orchard 地图分辨率0.025m、demo为0.05m；树级观察站位在 data_orchard 中不指定果实。

add_harvest_plugins(robot_xml, manifest) 返回新 URDF 文本：按当前 SRDF harvest_stow 注入 position 初值、追加机器人 PosePublisher、为每个目标生成 wrist3_Link→<id>_picked/bag 的 DetachableJoint。attach/detach/state 桥由 sim_bringup 按同一目标清单生成；没有源模型文件回写。

## 数据格式与坐标

data_orchard/assets.json（schema sim_worlds/data_orchard/v1）含 trees、targets、obstacles、来源/导出器/网格哈希；树/袋视觉为 Z-up 米制，袋果原点为 bag_bottom。targets 的碰撞盒中心有 map 系 collision_center 和模型局部 collision_center_local，尺寸 collision_size；这些不能互换。质量/惯量是均匀刚体假设，不是测量值。

demo.manifest（sim_worlds/harvest_demo/v1）包含两颗确定性袋果、树干/路标 obstacles；程序化 peach_orchard.manifest（sim_worlds/orchard_manifest/v1）则包含平台、目标和可达标记，当前不生成 obstacles 字段。reachable 是生成器几何粗筛，不是 MoveIt IK/轨迹执行成功。

demo/data_orchard stations.yaml 含 spawn{x,y,yaw} 和 stations[{id,nav_pose,...}]；data_orchard 另有 tree_id，demo 有 target_id。generate_field 的历史 stations 使用 tree_id/index/x/y/yaw/bag_count，联合 field 默认无任务服务器，不应直接作为当前 Mission 的 nav_pose 任务表。

map YAML 使用标准 Nav2 图像、分辨率、origin 和 trinary 阈值；导航图只投影配置高度带或树干代理，不等于机械臂的三维碰撞场景。scene_params 中平台几何供统一 xacro 映射，运行时工具档案由组合 launch 另行选择。

Blender/重建开发脚本、历史模型路径和渲染证据格式见 [offline-tools.md](offline-tools.md)。
