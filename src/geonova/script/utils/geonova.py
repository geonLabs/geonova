import os
import rospy
import rospkg
from sensor_msgs.msg import Image, Imu, NavSatFix
from message_filters import Subscriber, ApproximateTimeSynchronizer

import utils.yolo_models
import utils.image_tools

import time

class Geonova:
    def __init__(self):
        self.ros_pack_dir = rospkg.RosPack().get_path('geonova')
        self.model = rospy.get_param("model")
        self.save_dir = rospy.get_param("save_dir")
        self.model_path = os.path.join(self.ros_pack_dir,self.model)
        self.rgb_img_sub = Subscriber("/oak/rgb/image_raw", Image)
        self.stereo_img_sub = Subscriber("/oak/stereo/image_raw", Image)
        self.image_tools = utils.image_tools.image_tools()

        self.model = utils.yolo_models.yolo_v8(self.model_path)
        self.save_result_dir = os.path.join(self.ros_pack_dir, self.save_dir)

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
        rgb_image = self.image_tools.convert_image(rgb_msg)

        stereo_image = self.image_tools.convert_image(stereo_msg)
        results = self.model.model_inference(rgb_image)
        
        if results.boxes.xywh.numel() > 0:
            # self.image_tools.save_image(results.plot(), self.save_result_dir)
            # self.image_tools.save_image(rgb_image, self.save_result_dir)
            depth = self.image_tools.result_depth(stereo_image, results)
            print("")

        

    def stereo(self):
        pass

    
