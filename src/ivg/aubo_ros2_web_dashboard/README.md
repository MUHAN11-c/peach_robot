# aubo_ros2_web_dashboard

IVG 独立演示面板与 FastAPI 网关，默认 HTTP 8095、Foxglove 上游 127.0.0.1:8765、视频上游 8089。八个面板为门户、机械臂、视觉抓取、拉花、调试、监控、日志、设置；不进入 Peach harvest_system/lifecycle，Peach Web 位于 src/peach/peach_web。

## 当前入口及依赖缺口（2026-11-06）

当前源码保留两套网关入口，不能混同：

- `web_dashboard.launch.py` 启动 ivg_foxglove_bridge 和 `python3 -m aubo_ros2_web_dashboard.launch_gateway`。后者导入旧 ros_web_link.config/app，并从旧包 share 合并 JS 传输/渲染资源。本工作区已没有 ros_web_link 包；现有 src/ros2_web_link 使用另一套 ROSbridge SDK，不能据名称直接替换。因此这个组合入口尚不具备当前树中自包含、可启动的依据。
- console script `ivg_fastapi_static_gateway` 和 `python3 -m aubo_ros2_web_dashboard.fastapi_static_gateway` 使用本包 gateway.app.create_app。它不初始化 rclpy 节点，但工具几何/mesh 路由仍使用 ament 包资源索引，不能称为零 ROS 依赖。该入口本身也不补齐 UI 缺失的旧共享 JS。

本包 web/js 当前主要保留 UI，页面仍导入旧 transport/core/view3d 等共享模块；对应实现不在当前包中。2026-10-10 的 Foxglove 重构和 2026-10-13 的 ros_web_link 抽取是历史设计记录，不能作为本轮浏览器可用或性能验证。

## HTTP 与 ROS 契约

本地 gateway 提供 `/health`、`/api/v1/runtime`、`/api/v1/settings`（POST）、`/api/v1/tool-geometries`、`/api/ivg/robot-mesh/{pkg}/{path}`、`/api/ivg/proxy/web-video/*`、静态文件与 `/ws/foxglove` 代理。`config/defaults.yaml` 是本地网关/UI 默认配置；旧组合入口另外依赖旧包配置。

本地工具几何路由读取 ivg_description/config/tools.yaml，并有内置几何回退；组合入口的 gateway_routes.py 仍查 tool_changer/config/tools.yaml，当前资源已迁出，该路径不能返回相同的工具档案。web_video_server 不由组合 launch 启动，且 8089 与 ivg_pose_estimation Web 默认端口冲突。

Web 服务名/类型须与 ivg_interfaces 和实际服务端核对：视觉抓取单次服务为 `/execute_single_grasp`，循环 SetBool 只控制后续周期。UI 的调试 MoveXYZ 调用仍标为旧 demo_interface/srv/MoveToPose，而当前服务端为 ivg_interfaces/srv/MoveToPose；本轮只记录此差异，未修改运行逻辑。

Foxglove 桥实际监听地址/能力见 [ivg_foxglove_bridge](../ivg_foxglove_bridge/README.md)，当前默认 0.0.0.0:8765；8095 不是唯一监听外部接口的端口。

## 检查与运行边界

```bash
colcon build --packages-select aubo_ros2_web_dashboard ivg_foxglove_bridge
colcon test --packages-select aubo_ros2_web_dashboard
colcon test-result --verbose
npm --prefix src/ivg/aubo_ros2_web_dashboard test
```

package.xml 声明了 ament lint 依赖，但当前包无 test/ 或测试注册；npm test 使用 vitest --passWithNoTests，当前 UI 没有测试。历史 51 用例归属于已迁出的旧共享包，不代表当前工作树验证结果。

面板具有运动/IO 调用代码，真机运动和 SetIO 须操作员明确授权；启动 real 栈不构成授权。工作区禁止启动/调用驱动 dashboard；本面板也不是硬件急停通道。IVG 与 Peach 运行时须隔离 ROS 域。2026-11-06 本轮未启动网关、浏览器、ROS 或硬件。许可 Apache-2.0。
