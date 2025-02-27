import sys
sys.path.append("/usr/lib/python3.8/dist-packages/")
import numpy as np
np.bool=np.bool_
from ultralytics import YOLO

# Load a model
model = YOLO("/home/jm/workspace/KT_Project/new_geon_ws/src/geonova/models/version4.2_model_m_param_imgsz_1280_best.engine")  # load a custom model

# Validate the model
metrics = model.val(data="/home/jm/workspace/KT_Project/new_geon_ws/src/geonova/data/data_version4.2/model.yaml",imgsz=1280)
