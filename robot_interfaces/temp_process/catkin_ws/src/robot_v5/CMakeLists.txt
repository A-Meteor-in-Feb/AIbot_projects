cmake_minimum_required(VERSION 3.0.2)
project(robot_v5)


find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
)


catkin_python_setup()


catkin_package()

include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)

catkin_install_python(PROGRAMS
  scripts/executor.py
  scripts/mock_ros.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

