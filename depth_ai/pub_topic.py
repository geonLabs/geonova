import rospy
import numpy as np
import cv2
import depthai as dai
from datetime import timedelta
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

monocam_resolution = dai.MonoCameraProperties.SensorResolution.THE_800_P
rgb_resolution = dai.ColorCameraProperties.SensorResolution.THE_4_K

fps = 10

pipeline = dai.Pipeline()

rgb = pipeline.create(dai.node.ColorCamera)
left = pipeline.create(dai.node.MonoCamera)
right = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)
sync = pipeline.create(dai.node.Sync)
rgb_ctrl = pipeline.create(dai.node.XLinkIn)
xout = pipeline.create(dai.node.XLinkOut)
spatialCalc = pipeline.create(dai.node.SpatialLocationCalculator)

rgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
left.setBoardSocket(dai.CameraBoardSocket.CAM_B)
right.setBoardSocket(dai.CameraBoardSocket.CAM_C)

rgb.setFps(fps)
left.setFps(fps)
right.setFps(fps)

rgb.setResolution(rgb_resolution)
left.setResolution(monocam_resolution)
right.setResolution(monocam_resolution)

rgb.setIspScale(1, 2)

# rgb.setImageOrientation(dai.CameraImageOrientation.ROTATE_180_DEG)
# left.setImageOrientation(dai.CameraImageOrientation.ROTATE_180_DEG)
# right.setImageOrientation(dai.CameraImageOrientation.ROTATE_180_DEG)

xout.setStreamName("xout")
left.setCamera("left")
right.setCamera("right")
rgb_ctrl.setStreamName("rgb_ctrl")

sync.setSyncThreshold(timedelta(milliseconds=50))

stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.DEFAULT)
stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
stereo.setLeftRightCheck(True)
stereo.setSubpixel(True)
# stereo.setExtendedDisparity(True)
stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)

# 링크 연결
rgb_ctrl.out.link(rgb.inputControl)
rgb_ctrl.out.link(left.inputControl)
rgb_ctrl.out.link(right.inputControl)
left.out.link(stereo.left)
right.out.link(stereo.right)

rgb.video.link(sync.inputs["color"])
stereo.disparity.link(sync.inputs["disparity"])

sync.out.link(xout.input)

# disparity 값을 uint8로 변환
disparityMultiplier = 255.0 / stereo.initialConfig.getMaxDisparity()

startX, startY, width, height = 300, 0, 1320, 600

# ROS 노드 초기화
rospy.init_node('oak_camera_publisher', anonymous=True)

# ROS Publisher 생성
rgb_pub = rospy.Publisher('/oak/rgb/image_raw', Image, queue_size=10)
depth_pub = rospy.Publisher('/oak/stereo/image_raw', Image, queue_size=10)

# CvBridge 생성
bridge = CvBridge()

with dai.Device(pipeline) as device:
    controlQueue = device.getInputQueue("rgb_ctrl")

    ctrl = dai.CameraControl()
    ctrl.setAutoFocusMode(dai.CameraControl.AutoFocusMode.OFF)  # Auto focus
    ctrl.setAutoExposureEnable()  # Auto exposure
    ctrl.setAutoExposureRegion(startX, startY, width, height)

    controlQueue.send(ctrl)

    queue = device.getOutputQueue("xout", 30, True)

    while not rospy.is_shutdown():
        msgGrp = queue.get()
        for name, msg in msgGrp:
            frame = msg.getCvFrame()
            timestamp = rospy.Time.now()

            if name == "disparity":
                # frame = (frame * disparityMultiplier).astype(np.uint8)
                # frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
                ros_msg = bridge.cv2_to_imgmsg(frame, encoding="16UC1")
                # print(bridge.imgmsg_to_cv2(ros_msg, desired_encoding="passthrough"))
                ros_msg.header.stamp = timestamp
                depth_pub.publish(ros_msg)

            elif name == "color":
                ros_msg = bridge.cv2_to_imgmsg(frame, encoding="bgr8")
                ros_msg.header.stamp = timestamp
                rgb_pub.publish(ros_msg)

