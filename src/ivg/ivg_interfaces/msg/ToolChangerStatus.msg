# 快换盘状态消息
#
# 当前发布者 gripper_swap_worker 在启动、流程变更及每 5 秒发布软件工具状态，
# 没有轮询 DI/锁紧限位；initial_tool_id 或方向中的源工具也可补充此状态。
# 消费者：scene_attach_worker、Web 工具面板。不能据此证明实物已锁紧。
#

# header.stamp 为发布时刻，frame_id 当前固定为 tool_changer（逻辑标签）
std_msgs/Header header
# 当前连接的工具 ID，如 "gripper0"、"gripper2"、"suction_v1" 等，
# 与 tools.yaml 中的 tool_id 字段一致，空字符串表示未安装工具
string tool_id
# 当前连接的工具名称（人类可读），用于前端显示和日志记录
string tool_name
# 工具功能类型分类："gripper"（夹爪型）/ "suction"（吸盘型）/ "other"（其他），
# 用于切换策略的差异化处理（如 Gripper 使用 IO 控制开闭，Suction 使用气阀控制）
string tool_type
# 软件连接状态；当前通常由工具 ID 是否为空决定，不是限位开关反馈
bool is_connected
# 工具参数 JSON 字符串，包含工具特有的配置信息（如夹爪行程、最大夹持力、IO 引脚映射等），
# 解析格式与 tools.yaml 定义一致
string tool_parameters
