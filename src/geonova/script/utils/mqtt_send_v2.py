import os
import requests
import paho.mqtt.client as mqtt
import json
import uuid
from datetime import datetime

class PayloadSender:
    def __init__(self, results, img_path):
        self.results = results  # ✅ 한 이미지에 대한 검출 리스트
        self.img_path = img_path  # ✅ 한 개의 이미지 파일
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
        self.boxes_result = None
        self.events = []
        self.client = mqtt.Client()

    def __call__(self, *args, **kwds):
        self.recive_result()
        self.message_parser()
        self.configure_mqtt()
        self.upload_image()

    def recive_result(self):
        for data in self.results:
            box_values = ",".join(
                str(int(value)) if i in [2, 3, 4, 5] else f"{value:.2f}" if i == 1 else str(value)
                for i, value in enumerate(data[:6])
            )

            if self.boxes_result:
                self.boxes_result = f"{self.boxes_result},{box_values}"
            else:
                self.boxes_result = box_values

            x = data[7]
            y = data[6]

            event = {
                "eventID": str(uuid.uuid4()),
                "eventType": "SOC",
                "imageID": os.path.basename(self.img_path),  # ✅ 이미지 파일 이름 저장
                "timestamp": self.timestamp,
                "location": {
                    "x": str(x),
                    "y": str(y),
                },
                "eventContent": {
                    "track_id": "1",
                    "classified": str(data[0]),
                    "score": str(data[1])
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
