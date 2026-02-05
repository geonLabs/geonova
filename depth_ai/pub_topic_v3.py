import rospy
import depthai as dai
from datetime import timedelta
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

FPS = 30
SIZE = (1280, 800)

pipeline = dai.Pipeline()

# Cameras (v3)
rgb_cam = pipeline.create(dai.node.Camera)
left_cam = pipeline.create(dai.node.Camera)
right_cam = pipeline.create(dai.node.Camera)

rgb_cam.build(dai.CameraBoardSocket.CAM_A, sensorResolution=None, sensorFps=FPS)
left_cam.build(dai.CameraBoardSocket.CAM_B, sensorResolution=None, sensorFps=FPS)
right_cam.build(dai.CameraBoardSocket.CAM_C, sensorResolution=None, sensorFps=FPS)

# Outputs: 1280x800
rgb_out = rgb_cam.requestOutput(size=SIZE, type=dai.ImgFrame.Type.BGR888p, fps=FPS)
left_out = left_cam.requestOutput(size=SIZE, type=dai.ImgFrame.Type.GRAY8, fps=FPS)
right_out = right_cam.requestOutput(size=SIZE, type=dai.ImgFrame.Type.GRAY8, fps=FPS)

# Stereo + Sync
stereo = pipeline.create(dai.node.StereoDepth)
sync = pipeline.create(dai.node.Sync)
sync.setSyncThreshold(timedelta(milliseconds=120))

stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.DEFAULT)
stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)
stereo.setLeftRightCheck(True)
stereo.setSubpixel(True)
stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)

left_out.link(stereo.left)
right_out.link(stereo.right)

rgb_out.link(sync.inputs["color"])
stereo.depth.link(sync.inputs["depth"])  # depth(mm, uint16)

# ✅ (중요) 큐 생성은 start() 전에!
queue = sync.out.createOutputQueue(maxSize=2, blocking=False)

# (선택) 카메라 컨트롤 큐도 start() 전에 생성
rgb_ctrl_q = rgb_cam.inputControl.createInputQueue()
left_ctrl_q = left_cam.inputControl.createInputQueue()
right_ctrl_q = right_cam.inputControl.createInputQueue()

# 이제 start
pipeline.start()

# 컨트롤 보내기
ctrl = dai.CameraControl()
rgb_ctrl_q.send(ctrl)
left_ctrl_q.send(ctrl)
right_ctrl_q.send(ctrl)

# ROS
rospy.init_node("oak_camera_publisher", anonymous=True)
rgb_pub = rospy.Publisher("/oak/rgb/image_raw", Image, queue_size=2)
depth_pub = rospy.Publisher("/oak/stereo/depth_raw", Image, queue_size=2)
bridge = CvBridge()

while (not rospy.is_shutdown()) and pipeline.isRunning():
    msgGrp = queue.get()
    stamp = rospy.Time.now()

    for name, msg in msgGrp:
        frame = msg.getCvFrame()

        if name == "color":
            ros_msg = bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            ros_msg.header.stamp = stamp
            rgb_pub.publish(ros_msg)

        elif name == "depth":
            ros_msg = bridge.cv2_to_imgmsg(frame, encoding="16UC1")
            ros_msg.header.stamp = stamp
            depth_pub.publish(ros_msg)

