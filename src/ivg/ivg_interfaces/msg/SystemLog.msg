# 结构化系统日志消息
#
# 当前 system_monitor_node 只发布自身启动事件，不聚合全栈关键日志。
# Web 消费者的历史传输设计为 Foxglove；网关/共享 JS 的当前限制见 Web 包 README。
#

# 生产者填写的事件时间；当前监控器在 publishLog 中使用 now()
builtin_interfaces/Time timestamp

# 日志级别常量：调试信息，仅开发/调试时需要，生产环境通常屏蔽
uint8 LEVEL_DEBUG=0
# 日志级别常量：一般信息，正常操作的事件记录（如 "工具切换完成"）
uint8 LEVEL_INFO=1
# 日志级别常量：警告，潜在问题但不影响当前操作（如 "接近关节限位"）
uint8 LEVEL_WARN=2
# 日志级别常量：错误，操作失败或异常状态需要人工介入（如 "SDK 连接断开"）
uint8 LEVEL_ERROR=3

# 日志级别值：取值为 LEVEL_DEBUG / LEVEL_INFO / LEVEL_WARN / LEVEL_ERROR 之一
uint8 level
# 生产者填写的逻辑来源；当前启动日志为 system_monitor
string node_name
# 日志内容主体，纯文本描述，不包含二进制或特殊编码数据
string message
# 来源文件路径（可选），可用于在 IDE 中快速定位代码位置；空字符串表示不可用
string file
# 来源行号（可选）；当前监控器未填 file/line，消息默认值为空字符串/0
int32 line
