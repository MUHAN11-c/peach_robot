# percipio_camera

图漾工业相机 ROS 2 驱动，包含厂商 camport4 SDK 与项目使用的 launch/内参覆盖。
公有 ROS 组件为 `percipio_camera::PercipioCameraNodeDriver`；CMake 同时生成
`percipio_camera_node`，另安装 `list_devices`、`network_ip_config`。后者会改设备网络，
不是采摘启动入口。本说明以当前 launch 与 `src/percipio_camera_node.cpp` 为准，
不修改厂商源码。

## 启动与默认值

Peach 仅在 `camera_enabled=true` 且 `camera_frontend=percipio` 时，经 driver bringup
include `percipio_camera.launch.py`；stereo/replay 路径不启动本相机驱动。
两种实时前端使用同一设备，不能并行打开连接。

本项目 `percipio_camera.launch.py` 默认 IP `169.254.10.110`、`camera_name=camera`、
彩色与深度均为 640×480、配准开启、彩色点云开启、普通点云关闭，帧率控制目标 2.5。
目标值不证明实际相机到达率。它已不是仅 RGB 的默认配置；只采彩色时须显式关闭
深度与彩色点云。Jazzy 使用 `component_container` 加载组件，默认容器位于 `/camera`。

`percipio_rgbd.launch.py` 是项目 RGB-D 封装，强制开彩色、深度、配准与点云选项；
底层彩色点云模式会关闭普通灰度点云，最终发布 `depth_registered/points`。
`cam_base_cfg.launch.py`、`multi_cam.launch.py` 是另一组厂商示例，分辨率和设备默认值
不同，不等价于 Peach 部署。相机不能由标定工具或网页成功连接推断为已正确配准。

## 输出、QoS 与坐标

默认 `/camera` 名称空间下：

- `/camera/color/image_raw`：BGR8；`/camera/color/camera_info`：彩色内参。
- `/camera/depth/image_raw`：设备 C16 深度为 16UC1；另一 ABC16 格式为 16SC3，
  不能只按话题名假设它总是单通道深度。`/camera/depth/camera_info` 描述当前深度投影。
- `/camera/depth_registered/points`：彩色点云；普通点云模式为 `/camera/depth/points`。
- `/camera/device_event`：String，RELIABLE / TRANSIENT_LOCAL / depth1。

图像、CameraInfo、点云的 launch QoS 参数默认 `default`，映射为
`rmw_qos_profile_default`；可显式选择 `sensor_data` 等受支持 profile。
图像发布回调只有在该路图像存在订阅者时才同时发布 CameraInfo，单独订阅
CameraInfo 不会触发图像回调中的发布。

图像 stamp 直接由 SDK 流的微秒时间转换，不替换为 ROS 回调到达时间；不能据此
假定不同流同帧或设备时钟已与主机校准。frame_id 依 `camera_name` 生成，默认
`camera_{color,depth}_optical_frame`；内部 `/tf_static` 从 `camera_link` 建立流帧和
optical 旋转，外部腕到相机根的标定由 hand-eye 发布器负责。

原始 C16 数值没有在 ROS 图像发布时统一改为毫米。设备 `DepthScaleUnit`
决定 raw 到毫米的比例，启动日志会报告；本工作区 Percipio 配置常用 0.25，
Peach 感知/重建的 `depth_scale_unit` 必须匹配。不能把 16UC1 一律当毫米，
也不能将 stereo/replay 的比例直接套用到此设备。

## 彩色内参覆盖与配准

`color_camera_info_file` 默认读安装树 `share/percipio_camera/config/color_camera_info.yaml`；
源码事实源为 `config/color_camera_info.yaml`，由
[`apply_intrinsics`](../aubo_hand_eye_calibration/README.md) 校验写入。
修改后重新构建本包并重启相机；空路径或解析失败使用设备内参。

覆盖只替换发布的彩色 CameraInfo 的 D/K/R/P，宽高与 header 保留设备流值；
不会自动缩放 YAML 的 K，不改设备 Flash、深度 CameraInfo 或内部深度到彩图配准。
配准算法仍使用设备标定数据，须分别核对图像分辨率、覆盖内参与配准输出。

## 其它入口与验证边界

组件还订阅 `/camera/soft_trigger`（String）、`dynamic_config`（String）、`reset`
（Empty），均为 SensorDataQoS。这些是设备命令话题，不是 ROS 服务；日常采摘
不依赖手工发送。驱动没有 `set_camera_info` 服务，内参 GUI 使用 SAVE 后离线落盘。

CMake 链接随包 camport4 SDK 并安装其本机架构动态库；ROS/OpenCV 依赖走 Jazzy apt，
不要用 pip opencv-python 替换系统 OpenCV。当前 CMake 没有注册 BUILD_TESTING 检查，
package.xml 中列出 lint 依赖不代表 `colcon test` 实际执行了这些检查。

设备枚举、取帧、配准和单位须按本轮日志与话题检查分别验证。历史非 ROS 评测工具
见 [scripts/ps800_eval/README.md](scripts/ps800_eval/README.md)，不进入 colcon 构建，
其台架数字不代表当前部署或真实采摘精度。
