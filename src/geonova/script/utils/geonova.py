import rospy
from sensor_msgs.msg import Image, Imu, NavSatFix
from message_filters import Subscriber, ApproximateTimeSynchronizer

import utils.yolo_models
import utils.image_tools

import time

class Geonova:
    def __init__(self):
        self.model_path = rospy.get_param("model", "../models/yolov8n.pt")
        self.rgb_img_sub = Subscriber("/oak/rgb/image_raw", Image)
        self.stereo_img_sub = Subscriber("/oak/stereo/image_raw", Image)
        self.iamgetools = utils.image_tools.image_tools()
    
    def __call__(self):
        rospy.init_node("geonva", anonymous=True)
        rospy.loginfo("GeoNova Start")

        ats = ApproximateTimeSynchronizer(
            [self.rgb_img_sub, self.stereo_img_sub], 
            queue_size=30, 
            slop=0.1)

        ats.registerCallback(self.sync_callback)

        rospy.spin()

    def sync_callback(self, rgb_msg, stereo_msg):
        model = utils.yolo_models.model_load(self.model_path)

        rgb_image = self.iamgetools.convert_image(rgb_msg)
        # rgb_image = self.iamgetools.ros_image_to_numpy(rgb_msg)
        stereo_image = self.iamgetools.convert_image(stereo_msg)
        
        # start_time = time.time()
        resize_img = self.iamgetools.resize_with_padding(rgb_image)
        # rgb_vpi_img = self.iamgetools.flip_img(self.iamgetools.numpy_to_vpi_image(rgb_image))
        # resize_img = self.iamgetools.add_padding_to_original(rgb_vpi_img, 640, 640)
        # tensor_img = self.iamgetools.vpi_to_torch_tensor(resize_img)
        # end_time = time.time()
        # rospy.loginfo(f"Resize and padding processing time: {(end_time - start_time) * 1000:.2f} ms")

        model(resize_img, verbose=False)

    def stereo(self):
        pass

    