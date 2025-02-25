import rospy
import rospkg
import os
import requests
import paho.mqtt.client as mqtt
import json
import uuid
from datetime import datetime

class PayloadSender:
    def __init__(self, results, img_path):
        self.results = results
        self.img_path = img_path
        self.timestamp = None


        self.ip = "220.90.239.142"
        self.port = 1883
        self.username = "robot"
        self.password = "robot123"
        self.robot_id = "geon-1"
        self.topic = f"mrm/{self.robot_id}/eventAI/result"
        self.api_url = f"http://{self.ip}:7080/col/v1/image/saveImageFiles.do"
        self.header_key = "X-GEO-ROADAI-API"
        self.header_value = "Geon ce79e749650fb0c8595801d94c222bbc"

        self.client = mqtt.Client()


    def recive_result(self):
        pass