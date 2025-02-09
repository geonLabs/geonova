import sys
sys.path.append("/usr/lib/python3.8/dist-packages")
from ultralytics import YOLO

# Load a model
model = YOLO("/home/jm/workspace/KT_Project/new_geon_ws/src/geonova/models/best.pt")  # load an official model

# Export the model
model.export(format="engine",half=True)
