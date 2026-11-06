# sim_harvest

隔离仿真中的导航、观察与刚体采摘适配。Mission 经 Nav2 到站并串行派发操作；Grasp 经标准 MoveGroup/Pilz 执行、Gazebo 固定连接持果和重力落筐，不连接真机或调用 SetIO。

公开入口为 `/sim_harvest/run_harvest`（RunHarvest）、`pickup`（标准 Pickup）、`survey_scene`（SurveyScene）及限定收臂的 `move_to`（MoveTo）。运行入口仍是项目 `scripts/sim`；**当前 Gazebo 暂停**，这些接口和历史记录不代表当前版本闭环已验收。

模块、取消与阶段证据见 [架构](doc/architecture.md)，消息、许可、参数和结算口径见 [接口](doc/io.md)。test/ 只有官方 ament flake8/pep257 包装。
