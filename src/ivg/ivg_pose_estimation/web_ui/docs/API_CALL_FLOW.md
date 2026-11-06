# Web API 调用速览（当前实际面）

前端（`web_ui/index.html` + `scripts/app.js`）→ FastAPI（默认 `127.0.0.1:8089`，与手眼标定网关 8088 错开）→ ROS 2。

## 可用端点

| 端点 | 方法 | 作用 |
|---|---|---|
| `/status`, `/health` | GET | 服务与 ROS 桥状态 |
| `/exit` | POST | 退出 Web 进程 |
| `/api/capture_image` | POST | 软触发（`/camera/soft_trigger`）→ 缓存 depth/color 帧 |
| `/api/estimate_pose` | POST | 3D 位姿估计（调 `/estimate_pose` 服务） |
| `/api/estimate_pose_2d` | POST | 2D 位姿估计（调 `/estimate_pose_2d` 服务） |
| `/api/list_templates` 等 `/api/*template*` | POST/GET | 模板列表 / 读取 / 标准化 / 模板图下载 |
| `/api/debug/*` | POST | 调试图像、参数滑块、阈值持久化 |
| `/api/get_robot_status` 等运动/IO/抓取端点 | POST | **一律 501**（该估姿 Web 不发运动/IO） |

## 设计要点

- 运动与 IO 不经 Web：`/move_to_pose`、`/execute_single_grasp`、`/run_gripper_swap`
  等 ROS 服务自 2026-09-30 起存在于本仓 IVG 演示栈（`ivg_demo_services` /
  `tool_changer`，独立 DDS 域），但估姿 Web 不调用它们——对应 HTTP 端点保留并固定
  返回 501；独立 IVG 运动入口另见各包 README，真机操作须明确授权。
- 相机软触发是 `std_msgs/String` 话题 `/camera/soft_trigger`（Percipio 驱动），
  不是旧仓的 `SoftwareTrigger` 服务。
- 算法配置来源为包根 `config/pose_estimation.yaml`；旧 Web default_config.yaml 是兼容占位。滑块更新进程内配置，写 debug_thresholds.json，并通知 ROS update_params，不只是 UI 回显。
- 以上为 2026-11-06 静态核对；Web 使用同进程 rclpy 桥，未启动或重测 API。
