cmake_minimum_required(VERSION 3.0.2)
project(geonova)

# Find and include necessary packages
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  #message_generation
)

# Use setup.py for Python package installation
# Must be before generate_messages()
catkin_python_setup()

# Add message files
#add_message_files(
  #FILES
  #Detection.msg
  #DetectionArray.msg
#)

# Generate messages
#generate_messages(
  #DEPENDENCIES
  #std_msgs
#)

# Declare the catkin package
#catkin_package(
  #CATKIN_DEPENDS message_runtime
#)

# Include directories
include_directories(
  ${catkin_INCLUDE_DIRS}
)

# Install Python scripts (for execution)
catkin_install_python(PROGRAMS
  script/main.py
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
