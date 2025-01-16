#!/home/jm/workspace/python_venvs/yolov5_venv/bin python3

import rospy

class Geonova:
    def __init__(self):
        self.model = rospy.get_param("model", "../models/best.pt")
        
    
    def __call__(self):
        rospy.init_node("geonva", anonymous=True)
        rospy.loginfo("GeoNova Start")
        rospy.spin()
    