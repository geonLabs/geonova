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
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        self.ip = "220.90.239.142"
        self.port = 1883
        self.username = "robot"
        self.password = "robot123"
        self.robot_id = "geon-2"
        self.topic = f"mrm/{self.robot_id}/eventAI/result"
        self.api_url = f"http://{self.ip}:7080/col/v1/image/saveImageFiles.do"
        self.header_key = "X-GEO-ROADAI-API"
        self.header_value = "Geon ce79e749650fb0c8595801d94c222bbc"

        self.message = None
        self.boxes_result = ""
        self.events = []
        self.client = mqtt.Client()

    def __call__(self, *args, **kwds):
        if not self.results:
            return
        self.recive_result()
        if not self.events:
            return
        self.message_parser()
        self.configure_mqtt()
        self.upload_image()

    def recive_result(self):
        if not isinstance(self.results, list):
            return

        for obj in self.results:
            if not isinstance(obj, dict):
                continue

            timestamp = obj.get("Time") or self.timestamp
            self.timestamp = timestamp

            bounding_box = obj.get("BoundingBOX")
            if bounding_box and isinstance(bounding_box, (list, tuple)) and len(bounding_box) == 4:
                x1, y1, x2, y2 = [str(coord) for coord in bounding_box]
                box_data = f"{obj.get('ClassID', 'Unknown')},{obj.get('Confidence', '0')},{x1},{y1},{x2},{y2}"
                if self.boxes_result:
                    self.boxes_result = f"{self.boxes_result},{box_data}"
                else:
                    self.boxes_result = box_data

            event = {
                "eventID": obj.get("ID", str(uuid.uuid4())),
                "eventType": "SOC",
                "imageID": f"{obj.get('IMG_ID', 'Unknown')}.jpg",
                "timestamp": timestamp,
                "location": {
                    "x": obj.get("Longitude", "0"), #float
                    "y": obj.get("Latitude", "0"), #float
                },
                "eventContent": {
                    "track_id": "1",
                    "classified": str(obj.get("ClassID", "Unknown")),
                    "score": str(obj.get("Confidence", "0")),
                }
            }
            self.events.append(event)

    def message_parser(self):
        self.message = {
            "transactionId": f"{uuid.uuid4()}",
            "messageId": f"{uuid.uuid4()}",
            "robotId": self.robot_id,
            "timestamp": self.timestamp,
            "events": self.events
        }

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully")
        else:
            print(f"Connection failed with code {rc}")

    def configure_mqtt(self):
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.connect(self.ip, self.port, 60)
        self.client.loop_start()
        self.publish_message()
        self.client.loop_stop()

    def publish_message(self):
        try:
            payload = json.dumps(self.message)
            result = self.client.publish(self.topic, payload)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"Failed to publish message with result code {result.rc}")
        except Exception as e:
            print(f"Failed to publish message: {e}")

    def upload_image(self):
        headers = {self.header_key: self.header_value}

        if not self.img_path:
            return {"status": "error", "message": "Image path is not set"}

        try:
            with open(self.img_path, "rb") as image_file:
                files = {
                    "images": (os.path.basename(self.img_path), image_file, "image/jpg"),
                }
                data = {
                    "box_result": self.boxes_result,
                    "timestamp": self.timestamp
                }
                response = requests.post(self.api_url, headers=headers, files=files, data=data)

                if response.status_code == 200:
                    return {"status": "success", "response": response.text}
                else:
                    return {"status": "failure", "code": response.status_code, "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
