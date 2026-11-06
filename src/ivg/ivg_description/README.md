# ivg_description

IVG 工具模型与共享描述构建入口。`ivg_description.description.build_description` 默认生成 `gripper=none`、`hardware_mode=mock`、包含工作单元的 URDF；辅助函数还接受 `hardware_mode=none` 供无控制插件的描述使用。

`GRIPPERS` 当前为 none、gripper0、gripper1、gripper2、gripper1coffeecup、gripper1milkcup。工具由启动时的 xacro 参数选定；`urdf/aubo_e5.urdf.xacro` 组合本包 base/tools 模型并复用只读 AUBO ros2_control xacro。源码目录存在时优先从源码读取，随后使用 ament share。

`config/tools.yaml` 是快换轨迹和工具碰撞几何的档案，mesh URI 指向本包 `meshes/`。快换附着帧为 kuaihuan_Link；两个杯具档案用于场景/描述，不提供物理 dock 轨迹。CAD 推导值和预教值以配置中的来源说明为准，不能视作本轮硬件标定结果。

CMake 安装 urdf、meshes、config 及 Python 辅助模块。运行部署见 [ivg_bringup](../ivg_bringup/README.md)；动态快换只附着碰撞体，不重写此处 URDF，见 [tool_changer](../tool_changer/README.md)。
