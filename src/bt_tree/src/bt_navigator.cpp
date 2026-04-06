#include "rclcpp/rclcpp.hpp"
#include "behaviortree_cpp/bt_factory.h"
#include "behaviortree_cpp/loggers/bt_cout_logger.h"
#include "behaviortree_cpp/loggers/bt_file_logger_v2.h"
#include "behaviortree_cpp/loggers/groot2_publisher.h"
#include "nav2_msgs/action/navigate_to_pose.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include <chrono>
#include <thread>
#include <iomanip>
#include <sstream>
#include <cmath>
#include <memory>

using namespace BT;

// ==================== Action 节点类定义 ====================

// --- LogInfoNode ---
class LogInfoNode : public BT::ActionNodeBase
{
public:
    LogInfoNode(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ActionNodeBase(name, config) {}

    static BT::PortsList providedPorts()
    {
        return { BT::InputPort<std::string>("message") };
    }

    BT::NodeStatus tick() override
    {
        std::string message;
        if (getInput("message", message)) {
            RCLCPP_INFO(rclcpp::get_logger("bt_navigator"), "[LogInfo] %s", message.c_str());
        }
        return BT::NodeStatus::SUCCESS;
    }
    void halt() override {}
};

// --- LogWarnNode ---
class LogWarnNode : public BT::ActionNodeBase
{
public:
    LogWarnNode(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ActionNodeBase(name, config) {}

    static BT::PortsList providedPorts()
    {
        return { BT::InputPort<std::string>("message") };
    }

    BT::NodeStatus tick() override
    {
        std::string message;
        if (getInput("message", message)) {
            RCLCPP_WARN(rclcpp::get_logger("bt_navigator"), "[LogWarn] %s", message.c_str());
        }
        return BT::NodeStatus::SUCCESS;
    }
    void halt() override {}
};

// --- LogErrorNode ---
class LogErrorNode : public BT::ActionNodeBase
{
public:
    LogErrorNode(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ActionNodeBase(name, config) {}

    static BT::PortsList providedPorts()
    {
        return { BT::InputPort<std::string>("message") };
    }

    BT::NodeStatus tick() override
    {
        std::string message;
        if (getInput("message", message)) {
            RCLCPP_ERROR(rclcpp::get_logger("bt_navigator"), "[LogError] %s", message.c_str());
        }
        return BT::NodeStatus::SUCCESS;
    }
    void halt() override {}
};

// --- WaitNode ---
class WaitNode : public BT::ActionNodeBase
{
public:
    WaitNode(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ActionNodeBase(name, config) {}

    static BT::PortsList providedPorts()
    {
        return { BT::InputPort<double>("wait_duration") };
    }

    BT::NodeStatus tick() override
    {
        double wait_duration = 1.0;
        auto res = getInput("wait_duration", wait_duration);
        if (!res) {
            RCLCPP_WARN(rclcpp::get_logger("bt_navigator"), "[Wait] 未找到等待时间，使用默认值 1.0s");
        }
        
        std::this_thread::sleep_for(
            std::chrono::milliseconds(static_cast<int>(wait_duration * 1000)));
        return BT::NodeStatus::SUCCESS;
    }
    void halt() override {}
};

// 全局静态变量用于共享 ROS 节点
static rclcpp::Node::SharedPtr g_navigator_node;

// NavigateToPoseNode  

class NavigateToPoseNode : public BT::ActionNodeBase
{
public:
    using NavigateToPose = nav2_msgs::action::NavigateToPose;
    using GoalHandle = rclcpp_action::ClientGoalHandle<NavigateToPose>;

    NavigateToPoseNode(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ActionNodeBase(name, config), goal_sent_(false), finished_(false), success_(false)
    {
        if (!g_navigator_node) {
            RCLCPP_ERROR(rclcpp::get_logger("bt_navigator"), "全局节点未初始化");
            throw std::runtime_error("全局节点未初始化");
        }
        node_ = g_navigator_node;
        action_client_ = rclcpp_action::create_client<NavigateToPose>(node_, "navigate_to_pose");
    }

    ~NavigateToPoseNode() override {}

    static BT::PortsList providedPorts()
    {
        return {
            BT::InputPort<std::string>("goal"),
            BT::InputPort<double>("x"),
            BT::InputPort<double>("y"),
            BT::InputPort<double>("theta")
        };
    }

    BT::NodeStatus tick() override
    {
        if (finished_) {
            bool result = success_;
            finished_ = false;
            goal_sent_ = false;
            return result ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
        }

        if (!goal_sent_) {
            if (!action_client_->wait_for_action_server(std::chrono::seconds(1))) {
                RCLCPP_ERROR(node_->get_logger(), "[Nav] Nav2 action server 不可用");
                return BT::NodeStatus::FAILURE;
            }

            // 修复：正确获取端口值
            double x = 0.0, y = 0.0, theta = 0.0;
            
            auto res_x = getInput("x", x);
            auto res_y = getInput("y", y);
            auto res_theta = getInput("theta", theta);

            if (!res_x) {
                RCLCPP_WARN(node_->get_logger(), "[Nav] 未获取到 x 坐标，使用默认值 0.0");
            }
            if (!res_y) {
                RCLCPP_WARN(node_->get_logger(), "[Nav] 未获取到 y 坐标，使用默认值 0.0");
            }
            if (!res_theta) {
                RCLCPP_WARN(node_->get_logger(), "[Nav] 未获取到 theta，使用默认值 0.0");
            }

            // 如果具体端口没数据，尝试解析 goal 字符串
            if ((!res_x || x == 0.0) && (!res_y || y == 0.0)) {
                std::string goal_str;
                if (getInput("goal", goal_str)) {
                    sscanf(goal_str.c_str(), "%lf;%lf;%lf", &x, &y, &theta);
                    RCLCPP_INFO(node_->get_logger(), "[Nav] 从 goal 字符串解析坐标：[%.2f, %.2f, %.2f]", x, y, theta);
                }
            }

            auto goal_msg = NavigateToPose::Goal();
            goal_msg.pose.header.frame_id = "map";
            goal_msg.pose.header.stamp = node_->now();
            goal_msg.pose.pose.position.x = x;
            goal_msg.pose.pose.position.y = y;
            // 简单的欧拉角转四元数 (假设 theta 是 yaw)
            goal_msg.pose.pose.orientation.z = sin(theta / 2.0);
            goal_msg.pose.pose.orientation.w = cos(theta / 2.0);

            auto send_goal_options = rclcpp_action::Client<NavigateToPose>::SendGoalOptions();
            send_goal_options.result_callback = [this](const GoalHandle::WrappedResult& result) {
                this->finished_ = true;
                this->success_ = (result.code == rclcpp_action::ResultCode::SUCCEEDED);
                if (!this->success_) {
                    RCLCPP_ERROR(this->node_->get_logger(), "[Nav] 导航失败，错误码：%d", static_cast<int>(result.code));
                } else {
                    RCLCPP_INFO(this->node_->get_logger(), "[Nav] 导航成功!");
                }
            };

            RCLCPP_INFO(node_->get_logger(), "[Nav] 发送导航目标：[%.2f, %.2f, %.2f]", x, y, theta);
            action_client_->async_send_goal(goal_msg, send_goal_options);
            goal_sent_ = true;
            return BT::NodeStatus::RUNNING;
        }

        return BT::NodeStatus::RUNNING;
    }

    void halt() override
    {
        RCLCPP_INFO(node_->get_logger(), "[Nav] 收到 Halt 请求");
        finished_ = true;
        success_ = false;
        goal_sent_ = false;
    }

private:
    rclcpp::Node::SharedPtr node_;
    rclcpp_action::Client<NavigateToPose>::SharedPtr action_client_;
    bool goal_sent_;
    bool finished_;
    bool success_;
};

// ==================== 其他占位 Action 节点 ====================

class ComputePathToPoseNode : public BT::ActionNodeBase {
public:
    ComputePathToPoseNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ActionNodeBase(name, config) {}
    static BT::PortsList providedPorts() { return { BT::InputPort<std::string>("goal") }; }
    BT::NodeStatus tick() override { 
        RCLCPP_DEBUG(rclcpp::get_logger("bt_navigator"), "[ComputePathToPose] Simulating path computation"); 
        return BT::NodeStatus::SUCCESS; 
    }
    void halt() override {}
};

class FollowPathNode : public BT::ActionNodeBase {
public:
    FollowPathNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ActionNodeBase(name, config) {}
    static BT::PortsList providedPorts() { return { BT::InputPort<std::string>("path") }; }
    BT::NodeStatus tick() override { 
        RCLCPP_DEBUG(rclcpp::get_logger("bt_navigator"), "[FollowPath] Simulating path following"); 
        return BT::NodeStatus::SUCCESS; 
    }
    void halt() override {}
};

class ClearEntireCostmapNode : public BT::ActionNodeBase {
public:
    ClearEntireCostmapNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ActionNodeBase(name, config) {}
    static BT::PortsList providedPorts() { return { BT::InputPort<std::string>("service_name") }; }
    BT::NodeStatus tick() override { return BT::NodeStatus::SUCCESS; }
    void halt() override {}
};

class SpinNode : public BT::ActionNodeBase {
public:
    SpinNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ActionNodeBase(name, config) {}
    static BT::PortsList providedPorts() { return {}; }
    BT::NodeStatus tick() override { return BT::NodeStatus::SUCCESS; }
    void halt() override {}
};

class BackUpNode : public BT::ActionNodeBase {
public:
    BackUpNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ActionNodeBase(name, config) {}
    static BT::PortsList providedPorts() { return {}; }
    BT::NodeStatus tick() override { return BT::NodeStatus::SUCCESS; }
    void halt() override {}
};

// ==================== Condition 节点类定义 ====================

class IsObstacleDetectedNode : public BT::ConditionNode
{
public:
    IsObstacleDetectedNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ConditionNode(name, config) {}
    static BT::PortsList providedPorts() { return { BT::InputPort<double>("detection_range") }; }
    BT::NodeStatus tick() override { return BT::NodeStatus::FAILURE; }
};

class IsCancelRequestedNode : public BT::ConditionNode
{
public:
    IsCancelRequestedNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ConditionNode(name, config) {}
    static BT::PortsList providedPorts() { return {}; }
    BT::NodeStatus tick() override { return BT::NodeStatus::FAILURE; }
};

class IsStuckNode : public BT::ConditionNode {
public:
    IsStuckNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ConditionNode(name, config) {}
    static BT::PortsList providedPorts() { return {}; }
    BT::NodeStatus tick() override { return BT::NodeStatus::FAILURE; }
};

class GoalUpdatedNode : public BT::ConditionNode {
public:
    GoalUpdatedNode(const std::string& name, const BT::NodeConfiguration& config) : BT::ConditionNode(name, config) {}
    static BT::PortsList providedPorts() { return {}; }
    BT::NodeStatus tick() override { return BT::NodeStatus::FAILURE; }
};


// ==================== 导航器主类 ====================

class BtNavigator : public rclcpp::Node
{
public:
    BtNavigator() : Node("bt_navigator")
    {
        this->declare_parameter<std::string>("bt_xml_file", "");
        this->declare_parameter<int>("max_ticks", 200000);
        this->declare_parameter<int>("tick_interval_ms", 100);
        this->declare_parameter<int>("groot_port", 1666);
        this->declare_parameter<std::string>("map", "");

        std::string bt_xml_file = this->get_parameter("bt_xml_file").as_string();
        max_ticks_ = this->get_parameter("max_ticks").as_int();
        tick_interval_ms_ = this->get_parameter("tick_interval_ms").as_int();
        groot_port_ = this->get_parameter("groot_port").as_int();

        if (bt_xml_file.empty()) {
            RCLCPP_ERROR(this->get_logger(), "未指定行为树 XML 文件路径");
            throw std::runtime_error("未指定行为树 XML 文件路径");
        }

        RCLCPP_INFO(this->get_logger(), "========================================");
        RCLCPP_INFO(this->get_logger(), "BT Navigator 启动 (最终修复版)");
        RCLCPP_INFO(this->get_logger(), "XML 文件：%s", bt_xml_file.c_str());
        RCLCPP_INFO(this->get_logger(), "========================================");

        bt_xml_file_ = bt_xml_file;
    }

    void run()
    {
        g_navigator_node = shared_from_this();
        registerNodes();

        try {
            tree_ = factory_.createTreeFromFile(bt_xml_file_);
            RCLCPP_INFO(this->get_logger(), "行为树加载成功");
        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "加载行为树失败：%s", e.what());
            throw;
        }

        setupLogging();

        RCLCPP_INFO(this->get_logger(), "开始执行行为树...");

        NodeStatus status = NodeStatus::RUNNING;
        int tick_count = 0;

        while (rclcpp::ok() && status == NodeStatus::RUNNING && tick_count < max_ticks_) {
            status = tree_.tickOnce();
            tick_count++;

            if (tick_count % 10 == 0) {
                RCLCPP_INFO(this->get_logger(), "Tick %d - 状态：%s", tick_count, toStr(status).c_str());
            }

            // 处理 ROS 2 回调队列
            rclcpp::spin_some(shared_from_this());

            std::this_thread::sleep_for(std::chrono::milliseconds(tick_interval_ms_));
        }

        RCLCPP_INFO(this->get_logger(), "========================================");
        if (status == NodeStatus::SUCCESS) {
            RCLCPP_INFO(this->get_logger(), "行为树执行成功");
        } else if (status == NodeStatus::FAILURE) {
            RCLCPP_ERROR(this->get_logger(), "行为树执行失败");
        } else {
            RCLCPP_WARN(this->get_logger(), "行为树执行终止 (达到最大次数或中断)");
        }
        RCLCPP_INFO(this->get_logger(), "========================================");
    }

private:
    void registerNodes()
    {
        factory_.registerNodeType<LogInfoNode>("LogInfo");
        factory_.registerNodeType<LogWarnNode>("LogWarn");
        factory_.registerNodeType<LogErrorNode>("LogError");
        factory_.registerNodeType<WaitNode>("Wait");
        
        // 注册修复后的 NavigateToPose 节点
        factory_.registerNodeType<NavigateToPoseNode>("NavigateToPose");
        
        factory_.registerNodeType<ComputePathToPoseNode>("ComputePathToPose");
        factory_.registerNodeType<FollowPathNode>("FollowPath");
        factory_.registerNodeType<ClearEntireCostmapNode>("ClearEntireCostmap");
        factory_.registerNodeType<SpinNode>("Spin");
        factory_.registerNodeType<BackUpNode>("BackUp");

        factory_.registerNodeType<IsObstacleDetectedNode>("IsObstacleDetected");
        factory_.registerNodeType<IsStuckNode>("IsStuck");
        factory_.registerNodeType<GoalUpdatedNode>("GoalUpdated");
        factory_.registerNodeType<IsCancelRequestedNode>("IsCancelRequested");

        RCLCPP_INFO(this->get_logger(), "所有节点注册完成!");
    }

    void setupLogging()
    {
        logger_cout_ = std::make_unique<StdCoutLogger>(tree_);
        
        auto now = std::chrono::system_clock::now();
        auto now_time_t = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << "/tmp/bt_trace_" << std::put_time(std::localtime(&now_time_t), "%Y%m%d_%H%M%S");
        std::string btlog_path = ss.str() + ".btlog";

        logger_file_ = std::make_unique<FileLogger2>(tree_, btlog_path);
        groot2_publisher_ = std::make_unique<Groot2Publisher>(tree_, groot_port_);
        
        RCLCPP_INFO(this->get_logger(), "日志系统已初始化 (Groot2 Port: %d)", groot_port_);
    }

    BehaviorTreeFactory factory_;
    Tree tree_;
    std::unique_ptr<StdCoutLogger> logger_cout_;
    std::unique_ptr<FileLogger2> logger_file_;
    std::unique_ptr<Groot2Publisher> groot2_publisher_;
    int max_ticks_;
    int tick_interval_ms_;
    int groot_port_;
    std::string bt_xml_file_;
};

// ==================== 主函数 ====================

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);

    try {
        auto node = std::make_shared<BtNavigator>();
        node->run();
    } catch (const std::exception& e) {
        RCLCPP_ERROR(rclcpp::get_logger("bt_navigator"), "执行失败：%s", e.what());
        rclcpp::shutdown();
        return 1;
    }

    rclcpp::shutdown();
    return 0;
}