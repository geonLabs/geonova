cmake_minimum_required(VERSION 3.0.2)
project(geonova)

# Find and include necessary packages
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  message_generation  # ✅ 메시지 생성 패키지 추가
)

# Use setup.py for Python package installation
catkin_python_setup()

# ✅ 메시지 파일 추가
add_message_files(
  FILES
  Detection.msg
  Detections.msg
)

# ✅ 메시지 생성 설정
generate_messages(
  DEPENDENCIES
  std_msgs
)

# ✅ 패키지 선언 (message_generation 제거!)
catkin_package(
  CATKIN_DEPENDS message_runtime  # ✅ 여기에서 message_generation 제거!
)

# Include directories
include_directories(
  ${catkin_INCLUDE_DIRS}
)

# Install Python scripts (for execution)
catkin_install_python(PROGRAMS
  script/main.py
  script/utils/gps_filter.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}/script
)

# Install the utils Python module
install(
  DIRECTORY script/utils/
  DESTINATION ${CATKIN_PACKAGE_PYTHON_DESTINATION}/utils
  FILES_MATCHING PATTERN "*.py"
)

# Install the launch files
install(
  DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
  FILES_MATCHING PATTERN "*.launch"
)
