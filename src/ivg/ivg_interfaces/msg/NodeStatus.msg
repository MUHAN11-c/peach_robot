# 节点状态消息（系统健康监控）
#
# 当前发布者：ivg_demo_services/system_monitor_node，每秒把 RobotStatus
# 映射成一个逻辑名 aubo_driver 的状态；不枚举 ROS 图或检测各节点进程存活。
# 订阅者：Web Dashboard 监控面板
#

# 逻辑监控对象名；当前为 aubo_driver，不保证对应 ros2 node list 中的节点
string node_name
# 节点功能分类标签："driver" / "camera" / "vision" / "grasp" / "tool" / "web" / "system"，
# 用于监控面板分类显示和分组告警
string node_type
# 节点健康状态："online"（正常运行）/ "degraded"（功能降级或部分异常）/
# "offline"（节点已停止或失联）/ "error"（节点运行但存在不可恢复错误）
string status
# 状态说明；当前 offline/error/degraded 均会填写，online 为空
string error_message
# 监控器发布本消息的时刻，不是底层 RobotStatus 的最后接收时刻
builtin_interfaces/Time last_heartbeat
# system_monitor_node 启动以来的秒数，不随 online/degraded 等状态重置
float64 uptime_sec
