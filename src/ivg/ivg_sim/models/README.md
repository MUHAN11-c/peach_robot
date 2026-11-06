# ivg_sim models（YCB 对象库）

16 个 YCB 对象的 Gazebo SDF 模型（apple / banana / bleach_cleanser / bowl /
chips_can / cracker_box / gelatin_box / master_chef_can / mustard_bottle /
pitcher_base / potted_meat_can / pudding_box / sugar_box / tomato_soup_can /
tuna_fish_can / windex_bottle）。

## 分发口径

- **入库**：每对象的 `model.sdf` + `model.config` + `LICENSE_YCB`（CC BY 4.0）。
- **不入库**：`meshes/`（textured.dae / collision.dae / texture_map.png，
  全库约 118MB）——git 忽略，clone 后执行 `./fetch_ycb.sh` 恢复（或从
  备份拷贝）。缺失 meshes 时 gz 报 `Unable to find uri` / 渲染失败。
- 来源：YCB 对象集 SDF 转换（model.config 署名 Markus Vieth）；上游镜像
  如 <https://github.com/CentralLabFacilities/gazebo_ycb>（meshes 与本
  库一致，fetch 脚本默认从该仓库取）。

## 历史记录

2026-09-29 为本对象库入库日期。该目录是 Gazebo 对象资源，不是抓取模型 checkpoint 库；当前评分工具使用 ivg_sim 生成的 GT manifest，不消费模型仓库的 test_data。网格是否完整须按实际资源核对，本轮未下载或启动渲染。
