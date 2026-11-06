# ivg_pose_estimation

模板匹配 6D 估姿（旁路，非采摘）。IDL 走 `ivg_interfaces`，不进 `harvest_system` / lifecycle。

## 分段流水线（2026-09-29 前沿化轮）

```
Preprocessor(深度带连通域) → FeatureExtractor
  → Segmenter（分割段，可换）      → Matcher（匹配段，可换）     → PoseEstimator.estimate_pose
     depth_band（默认，轻量兜底）     geometric（默认，距离/IoU）
     rembg_u2net（u2net 显著性）     dinov2_template（DINOv2 嵌入
     mobile_sam（MobileSAM 点提示）    检索，FoundPose/CNOS 范式）
```

- 段选型在 `config/pose_estimation.yaml`（`segmenter.backend` / `matcher.backend`），
  Web 的 `use_rembg=true` 临时选 rembg；false 仅在配置档为 rembg 时退回 depth_band，其他配置档保持原样。
- `dinov2_template` 首次使用对每工件模板库离线建嵌入索引
  （`<模板目录>/.dinov2_index.npz`，模板更新自动重建；DINOv2 权重经
  torch.hub 首次下载缓存至 `~/.cache/torch/hub`）。
- 单位单源：`camera.depth_scale`（Percipio 0.00025）、
  `calibration.translation_unit`（mm|m|auto）；深度换算只在边界发生。
- `EstimatePose` 请求/响应带 `std_msgs/Header`（响应 stamp=图像采集时刻、
  frame=`base_link`；TF 同 stamp 查询，失败回退 latest+WARN）。

## 启动

相机图像与手眼 TF 须由外部提供；本包 launch 和当前 ivg_bringup 均不启动相机或手眼外参发布器。

```bash
source /opt/ros/jazzy/setup.bash
cd /home/mu/Desktop/aubo_e5_jazzy_ws
colcon build --packages-select ivg_interfaces ivg_pose_estimation
source install/setup.bash

ros2 launch ivg_pose_estimation ivg_pose_estimation.launch.py
# 另终端 Web（默认 http://127.0.0.1:8089/，与手眼标定网关 8088 错开；
# 注意 web_dashboard 栈的 web_video_server 上游也是 8089——同机并行会撞口，错开一方）
ros2 launch ivg_pose_estimation ivg_pose_estimation_web.launch.py
```

订 `/camera/{color,depth}/image_raw`；软触发发 `std_msgs/String` 到 `/camera/soft_trigger`。`T_B_C` 查 `base_link` ← `camera_color_optical_frame`。

Web 的运动/IO/抓取 HTTP 返回 **501**，该旁路只提供模板/算法调试，不能由此视作运动入口。独立 IVG 运动链见 ivg_demo_services/ivg_graspnet；真机操作须另有明确授权。

**Web 写端点认证**（2026-09-29 起）：`/exit`、`/api/save_template_pose`、
`/api/standardize_template`、`/api/debug/update_params`、
`/api/debug/save_thresholds` 需认证——同源 UI 自动携带 `vpe_auth`
SameSite=Strict cookie（零改动）；curl 带 `-H "X-Auth-Token: <token>"`
（token 打印在启动日志；环境变量 `VPE_WEB_TOKEN` 可固定）。跨域 CORS
已收紧为同源。

模板根：显式 `template_root` → `VPE_TEMPLATE_ROOT` → app_config.json（仅 Web 侧）→ 解析器找到的 templates 目录。setup.py 当前未安装 templates/；脱离源码部署时须显式提供现存模板目录，不能假定 share/templates 自包含。

数学工具（四元数/旋转矩阵/RPY）统一来自 `scipy.spatial.transform.Rotation`；rembg 抠图与 MobileSAM 分割走 `pipeline/segmenters/`（依赖 venv 内 rembg/onnxruntime/ultralytics；注册表可能跳过不可导入的档，选用未注册档会报错，不能保证统一自动降级）。`u2net.onnx`（约 168MB）与 `mobile_sam.pt`（约 39MB）**不随 git 分发**：执行 `models/fetch_u2net.sh` / `models/fetch_mobile_sam.sh`（后者仍探测旧 `peach_harvester/model/` 路径，当前树不存在时转为下载；当前本地权重在 `peach_scene_perception/model/`，离线拷贝见 models README；u2net 也可首用时 rembg/pooch 下载）。运行时 `U2NET_HOME` 指向包内 `models/`。

许可：MobileSAM/SAM2 Apache-2.0；ultralytics AGPL-3.0（库级内部研究使用）；DINOv2 Apache-2.0；rembg MIT（u2net 权重随上游）。商用替换：默认档（depth_band+geometric）无第三方模型依赖。

独立栈入口见 [IVG 源码导航](../README.md)；与 Peach 主链的边界见 [peach_bringup 架构](../../peach/peach_bringup/doc/architecture.md)。评估基线 `campaign/20260929_ivg_refactor/report.md`（2026-10-10 清理轮已删，git 历史可查：dinov2 检索 14/14；分割学习档棚拍口径未达标，默认档不切换）。

当前五个服务为 estimate_pose、estimate_pose_2d、list_templates、standardize_template、update_params；Web 使用同进程 rclpy 桥 algorithm_http_server_node，不是 ROSbridge WebSocket。当前 test/ 只有官方 flake8/pep257；2026-11-06 本轮未启动算法/相机/Web，历史基线不代表当前验证。
