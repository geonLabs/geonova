import rospy
from sensor_msgs.msg import Image, Imu, NavSatFix
from message_filters import Subscriber, ApproximateTimeSynchronizer

import yolo_models

class Geonova:
    def __init__(self):
        self.model_path = rospy.get_param("model", "../models/best.pt")
        
    
    def __call__(self):
        rospy.init_node("geonva", anonymous=True)
        rospy.loginfo("GeoNova Start")

        rgb_img_sub = Subscriber("/oak/rgb/image_raw", Image)

        rospy.spin()
    
    def model(self):
        model = yolo_models.model_load(self.model_path)        
        postprocessing = ""
        pass

    def stereo(self):
        pass