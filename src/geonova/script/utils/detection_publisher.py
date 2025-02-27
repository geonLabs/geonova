import rospy
from geonova.msg import Detections, Detection  
import os

class DetectionPublisher:
    def __init__(self):
        self.pub = rospy.Publisher("detections_topic", Detections, queue_size=10)

    def publish_detections(self, gps_coordinate, img_path):
        """
        gps_coordinate: List of lists containing detection data.
        Format: [[class_id, confidence, x1, y1, x2, y2, object_lat, object_lon], ...]
        """
        if not gps_coordinate or len(gps_coordinate) == 0:
            return

        detections_msg = Detections()
        detections_msg.img_path = img_path
        detections_msg.img_name = os.path.basename(img_path)

        for data in gps_coordinate:
            detection = Detection()
            detection.classid = int(data[0])      # class_id
            detection.conf = float(data[1])       # confidence
            detection.x1 = int(data[2])           # x1
            detection.y1 = int(data[3])           # y1
            detection.x2 = int(data[4])           # x2
            detection.y2 = int(data[5])           # y2
            detection.object_lat = float(data[6]) # object_lat
            detection.object_lon = float(data[7]) # object_lon

            detections_msg.detections.append(detection)

        # rospy.loginfo(f"Publishing {len(detections_msg.detections)} detections with GPS")
        self.pub.publish(detections_msg)
