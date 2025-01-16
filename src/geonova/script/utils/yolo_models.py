from ultralytics import YOLO

def model_load(model_path):
    return YOLO(model_path)
