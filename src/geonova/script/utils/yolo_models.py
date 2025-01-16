from ultralytics import YOLO

def model_load(model_path):
    return YOLO(model_path)

def model_inference(resize_img, model):
    
    pass