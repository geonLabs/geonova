import sys
sys.path.append("/usr/lib/python3.8/dist-packages")
from ultralytics import YOLO

# Load a model
model = YOLO("/home/jm/workspace/KT_Project/new_geon_ws/src/geonova/models/version4.2_model_m_param_imgsz_1280_best.pt")  # load an official model

# Export the model
model.export(format="engine",int8=True, data="/home/jm/workspace/KT_Project/new_geon_ws/src/geonova/data/data_version4.2/model.yaml", imgsz=1280)
