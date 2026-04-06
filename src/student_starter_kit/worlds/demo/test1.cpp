#include <behaviortree_cpp_v3/bt_factory.h>
#include <iostream>

// 👇 1. 这里是你提供的代码
class ApproachObject : public BT::SyncActionNode
{
public:
  ApproachObject(const std::string& name) :
      BT::SyncActionNode(name, {})
  {}

  BT::NodeStatus tick() override
  {
    std::cout << "ApproachObject: " << this->name() << " is running!" << std::endl;
    // 这里可以调用真实的机器人移动代码，例如：robot.moveForward();
    return BT::NodeStatus::SUCCESS;
  }
};

int main()
{
    // 2. 创建工厂
    BT::BehaviorTreeFactory factory;

    // 3. 【关键】注册你的自定义节点
    // 字符串 "ApproachObject" 必须和 Groot XML 里的 <Action ID="ApproachObject" /> 一致
    factory.registerNodeType<ApproachObject>("ApproachObject");

    // 4. 加载 XML 文件 (你在 Groot 里画的那个文件)
    // 路径要改为你实际保存 xml 的路径
    std::string xml_file = "/home/qinghe/ros2-demo_ws/src/student_starter_kit/worlds/demo/test1.xml"; 
    
    try {
        BT::Tree tree = factory.createTreeFromFile(xml_file);
        
        // 5. 运行行为树
        while (true) {
            BT::NodeStatus status = tree.tickRoot();
            if (status == BT::NodeStatus::SUCCESS) {
                std::cout << "Tree finished successfully!" << std::endl;
                break;
            }
            if (status == BT::NodeStatus::FAILURE) {
                std::cout << "Tree failed!" << std::endl;
                break;
            }
            // 控制循环频率，避免占用 100% CPU
            usleep(10000); 
        }
    } catch (std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}