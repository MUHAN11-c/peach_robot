# Blender 与重建开发工具索引

2026-11-06 源码盘点。blender/ 和 reconstruction/ 不在 setup.py 的 Python 包或 console scripts 列表，当前 launch 不自动调用。它们仍承担资产重导出与历史证据重现，不能整目录视为冗余。历史 [PLAN](../reconstruction/PLAN.md) 和 [RESULTS](../reconstruction/RESULTS.md) 按原日期理解，不作为当前 Gazebo/视觉闭环的成功证据。

## 当前资产导出

blender/export_data_orchard.py 在 Blender 4.5 打开现有 v11 blend 后使用 --out（必填）、--trees（默认0/1）、--leaf-ratio（默认0.20）。输出必须在 peach_sim 内。它保留原袋果几何、只减面叶片，提取实际枝干网格环圆柱，写 Z-up GLB 与 assets.json；材料会在进程内适配，但不保存回输入 blend。已有来源、哈希及复现命令见 [SOURCE](../worlds/data_orchard/SOURCE.md)。

blender/color_bunker.py 使用 --source/--out 将来源 STL 转成着色 GLB，来源与名义缩放见 [BUNKER_SOURCE](../../sim_description/meshes/BUNKER_SOURCE.md)。blender/build_assets.py 是旧树/袋资产生成器（--out/--textures），不能用它覆盖当前 data_orchard 的每果数据。blender/export_field_to_gz.py 将已有整园 blend 导出预览 GLB（--out、可选保留背景/减面）；整体网格没有独立可移除袋果。

## 数据、先验与参考观测

- audit_real_features.py：遍历数据文件，--dataset/--output/--workers，记录文件哈希、深度统计和图像空间代理，不将代理当叶片实测。
- audit_sources.py：历史多模态抽样、项目记录汇总和联系图，随后调用 measure_reference_leaves；顶层即执行并写 evidence，不应作为无副作用库导入。
- analyze_reference.py：历史参考帧的检测/分割与几何量测，--dataset/--frames，输出 evidence/reference_measurements.json。
- measure_reference_leaves.py：读取 prompts、MobileSAM 分割，写参考叶片证据；observed_foliage.py 根据掩膜/深度构造可见局部叶面，不能推断不可见整树叶分布。
- measure_priors.py：数据集/VOC 与历史现场 fixture 的分位统计，默认写 evidence/priors.json，--full 扩大注释样本；distributions.py 读取分位统计做可复现抽样并构造果袋相容尺寸。

上述工具含固定 /home/mu/Downloads 数据路径。analyze_reference、validate_perception、evaluate_matrix、measure_reference_leaves 还保留旧 peach_harvester/model 路径，ROOT/HERE 父级计算也沿用旧布局；当前目录下不能视为可直接运行的模型入口。measure_priors 的旧 peach_arm/test/fixtures/field_pregrasp_cases.yaml 当前不存在，audit_sources 的历史记录目录也不属于当前测试数据契约。修改前必须定位真实来源及模型并重验，不能静默补空统计或沿用旧标签。

## 建模和渲染

- build_scene.py：主建模/保存入口，参考/近景/整园机位，validation/field 规模，--out、--build-only、--lighting、--samples、--width、--no-grass。它读 evidence 中的先验，树形和隐藏结构仍为推断。
- geometry.py：纸袋、连通枝、叶片及实例网格；materials.py / make_textures.py：材质与程序纹理；lighting.py / lighting_apply.py：预设数据校验和 Blender 场景应用；occlusion.py / viewpoints.py：遮挡位置和停走视角纯核。这里的视角/工具尺度是离线管线参数，不替代当前 sim_harvest 运动计划。
- render_saved.py：读取当前已打开 blend，按保存 manifest 选参考/近景/整园相机并重新渲染；会写 out/scene_manifest.json、RGB 与 EXR，不重建几何。
- run_matrix.py：已保存 blend × 光照 × 轨迹，支持 --max-views/--subset-per-level/--view-kinds/--skip-reference/--skip-existing；默认量级大，产物含 trajectory 和每视角 RGB/Depth/IndexOB/Position。
- render_evidence.py：成功渲染后保存每视角文件哈希与 blend/光照/渲染设置；validate_render_set 拒绝缺文件、内容变更或混合上下文。
- depth_io.py：区分射线距离、光轴深度和米制→uint16毫米导出；输出中的无效0不得当背景。
- build_bag_assets.py / export_bag_assets.py：分别构造独立袋果评审资产、从已验证场景导出三种袋果；不是当前 data_orchard 导出器的替代。
- render_feature_details.py、make_appearance_board.py、make_review_boards.py、compare_reference_scene.py、compare_real_features.py、compare_dataset_depth.py：细节图、评审板、参考关联与总体深度/尺寸比较。各有固定输出/数据假设，图像比较不等于配准精度或物理采摘证明。

## 独立检查与结果

validate_geometry.py 对当前打开 blend 检查有限网格、封闭袋和内部果实包容，顶层即运行并写 blend 同目录 geometry_validation.json；并非穷举叶/枝/袋全部相交。validate_real_features.py 检查保存模型的网格连接等约束，可指定 blend；check_modeling_blender.py、check_real_features_blender.py 是开发期 Blender unittest 入口，未注册进 colcon test。

validate_perception.py 读取渲染/IndexOB 与原模型计算检测/框提示分割；evaluate_matrix.py 聚合光照、连续覆盖率桶与视角序列，--gate 读取冻结基线，--write-baseline 会覆盖基线。它们仍带上节所述旧模型路径，旧分数不能当作当前 FastSAM 或仿真 overlay 的成绩。

这些脚本部分在导入时就读数据、改 Blender 场景或写文件；静态盘点只解析源码，不导入它们探测。运行前使用新输出目录并保留输入/版本/模型哈希，入口及暂停规则仍以 [项目 README](../../README.md) 为准。
