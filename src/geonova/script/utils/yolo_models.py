import rospy
if rospy.get_param("tensorrt"):
    import sys
    # local tensorrt import path
    sys.path.append("/usr/lib/python3.8/dist-packages/")
    import tensorrt
import numpy as np
np.bool=np.bool_
from ultralytics import YOLO


class yolo_v8:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.verbose = rospy.get_param("verbose", False)
        self.model_cls_len = rospy.get_param("model_cls_len", 19)

    def model_inference(self, img):
        results = self.model(
            img, 
            device=0, 
            stream=True,
            stream_buffer=True,
            verbose=self.verbose,
            imgsz=(1280,1280),
            # conf=0.85,
            classes=[i for i in range(self.model_cls_len) if i != 1]
            )
        
        return list(results)[0]
