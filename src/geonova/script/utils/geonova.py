import os
import rospy
import rospkg
from sensor_msgs.msg import Image, Imu, NavSatFix
from message_filters import Subscriber, ApproximateTimeSynchronizer
# from ublox_msg.msg import NavPVT
from geometry_msgs.msg import QuaternionStamped

import utils.yolo_models
import utils.image_tools
import utils.mv_tools
import utils.mqtt_send

import time

class Geonova:
    def __init__(self):
        self.ros_pack_dir = rospkg.RosPack().get_path('geonova')
        self.model = rospy.get_param("model")
        self.save_dir = rospy.get_param("save_dir")
        self.model_path = os.path.join(self.ros_pack_dir, self.model)
        
        self.rgb_topic = rospy.get_param("rgb_topic", "/oak/rgb/image_raw")
        self.stereo_topic = rospy.get_param("stereo_topic", "/oak/stereo/image_raw")
        self.imu_topic = rospy.get_param("imu_topic", "/imu/data")
        self.gps_topic = rospy.get_param("gps_topic", "/fix")
        # self.gps_navpvt = rospy.get_param("gps_navpvt", "/ublox/navpvt")
        self.gps_navpvt = rospy.get_param("gps_navpvt", "/heading")
        
        self.rgb_img_sub = Subscriber(self.rgb_topic, Image)
        self.stereo_img_sub = Subscriber(self.stereo_topic, Image)
        self.imu_sub = Subscriber(self.imu_topic, Imu)
        self.gps_sub = Subscriber(self.gps_topic, NavSatFix)
        self.gps_navpvt_sub = Subscriber(self.gps_navpvt, QuaternionStamped)


        self.image_tools = utils.image_tools.image_tools()

        self.vision_model = utils.yolo_models.yolo_v8(self.model_path)
        self.save_result_dir = os.path.join(self.ros_pack_dir, self.save_dir)

    def __call__(self):
        rospy.init_node("geonva", anonymous=True)
        rospy.loginfo("GeoNova Start")
        ats = ApproximateTimeSynchronizer(
            [
                self.rgb_img_sub, 
                self.stereo_img_sub,
                self.imu_sub,
                self.gps_sub,
                self.gps_navpvt_sub
            ], 
            queue_size=30, 
            slop=0.1)

        ats.registerCallback(self.sync_callback)
        rospy.spin()

    def sync_callback(self, rgb_msg, stereo_msg, imu_msg, gps_msg, gps_navpvt_sub):
    # def sync_callback(self, rgb_msg, stereo_msg, imu_msg, gps_msg):
        rgb_image = self.image_tools.convert_image(rgb_msg)

        stereo_image = self.image_tools.convert_image(stereo_msg)
        results = self.vision_model.model_inference(rgb_image)
        
        if results.boxes.xywh.numel() < 1:
            return
        
        depth = self.image_tools.result_depth(stereo_image, results)

        if depth is None:
            return
        
        img_name = self.image_tools.save_image(rgb_image, self.save_result_dir, results)
        #img_name = self.image_tools.save_image(results.plot(line_width=2, font_size=2), self.save_result_dir, results)

        if img_name is None:
            return
        
        gps_check = utils.mv_tools.CalCoordinate(imu_msg, gps_msg, depth, gps_navpvt_sub)
        gps_coordinate = gps_check()

        if gps_coordinate is None:
            return
        
        payloader = utils.mqtt_send.PayloadSender(gps_coordinate, img_name)
        payloader()
