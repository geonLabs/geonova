import sys
sys.path.append("/usr/lib/python3.8/dist-packages/")
import tensorrt
import numpy as np
np.bool=np.bool_
from ultralytics import YOLO


class yolo_v8:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
    
    def model_inference(self, img):
        results = self.model(
            img, 
            device=0, 
            stream=True,
            stream_buffer=True,
            verbose=False,
            imgsz=1280,
            conf=0.85,
            classes=[0,2,3,4,5]
            )
        return list(results)[0]
