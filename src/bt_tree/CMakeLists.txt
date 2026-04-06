cmake_minimum_required(VERSION 3.8)
project(bt_tree)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(behaviortree_cpp REQUIRED)

add_executable(bt_navigator src/bt_navigator.cpp)
ament_target_dependencies(bt_navigator
  rclcpp
  rclcpp_action
  nav2_msgs
  behaviortree_cpp
)

install(TARGETS
  bt_navigator
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  behavior_trees
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

