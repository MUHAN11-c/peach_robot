// 场景附着 Worker — 将软件工具状态同步到 MoveIt 附着碰撞体。
// 工具档案/mesh 来自 ivg_description；默认附着帧 kuaihuan_Link。
// 不读取本包旧静态 URDF、不发布 robot_description；set_display_tool 只检查一致性。
#ifndef TOOL_CHANGER__SCENE_ATTACH_WORKER_HPP_
#define TOOL_CHANGER__SCENE_ATTACH_WORKER_HPP_

#include <map>
#include <memory>
#include <string>
#include <vector>

#include <geometry_msgs/msg/pose.hpp>
#include <ivg_interfaces/msg/tool_changer_status.hpp>
#include <ivg_interfaces/srv/change_tool.hpp>
#include <moveit_msgs/msg/attached_collision_object.hpp>
#include <moveit_msgs/msg/planning_scene.hpp>
#include <rclcpp/rclcpp.hpp>
#include <shape_msgs/msg/mesh.hpp>
#include <std_msgs/msg/string.hpp>

namespace tool_changer
{

class SceneAttachWorker : public rclcpp::Node
{
public:
  explicit SceneAttachWorker(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());
  ~SceneAttachWorker() override = default;

private:
  struct ToolGeometry
  {
    shape_msgs::msg::Mesh mesh_collision;
    geometry_msgs::msg::Pose attach_offset;  // 工具相对附着帧的偏移
    std::vector<std::string> touch_links;    // 附着时豁免碰撞的 link 列表
  };

  void loadToolConfig();
  shape_msgs::msg::Mesh loadMesh(const std::string & resource_path);

  void onToolStatus(const ivg_interfaces::msg::ToolChangerStatus & msg);

  void attachToolToScene(const std::string & tool_id);
  void detachToolFromScene(const std::string & tool_id);
  void removeWorldToolObject(const std::string & tool_id);

  void onSceneAttach(
    const std::shared_ptr<ivg_interfaces::srv::ChangeTool::Request> req,
    std::shared_ptr<ivg_interfaces::srv::ChangeTool::Response> resp);
  void onSceneDetach(
    const std::shared_ptr<ivg_interfaces::srv::ChangeTool::Request> req,
    std::shared_ptr<ivg_interfaces::srv::ChangeTool::Response> resp);
  void onSetDisplayTool(
    const std::shared_ptr<ivg_interfaces::srv::ChangeTool::Request> req,
    std::shared_ptr<ivg_interfaces::srv::ChangeTool::Response> resp);


  std::map<std::string, ToolGeometry> tool_geometries_;
  rclcpp::Publisher<moveit_msgs::msg::PlanningScene>::SharedPtr planning_scene_pub_;
  rclcpp::Publisher<moveit_msgs::msg::AttachedCollisionObject>::SharedPtr attached_object_pub_;
  rclcpp::Subscription<ivg_interfaces::msg::ToolChangerStatus>::SharedPtr tool_status_sub_;

  rclcpp::Service<ivg_interfaces::srv::ChangeTool>::SharedPtr scene_attach_srv_;
  rclcpp::Service<ivg_interfaces::srv::ChangeTool>::SharedPtr scene_detach_srv_;
  rclcpp::Service<ivg_interfaces::srv::ChangeTool>::SharedPtr display_tool_srv_;

  std::string attach_frame_{"kuaihuan_Link"};
  std::string modeled_tool_;
  std::string current_attached_tool_;
};

}  // namespace tool_changer

#endif  // TOOL_CHANGER__SCENE_ATTACH_WORKER_HPP_
