import rospy
import rospkg
import os
import requests
import paho.mqtt.client as mqtt
import json
import uuid
from datetime import datetime

class PayloadSender:
    def __init__(self, results):
        self.results = results
        self.events = []
        self.boxes_result = []
        self.message = None

        self.img_name = None
        self.pkg_dir = rospkg.RosPack().get_path('geonova')
        self.save_dir = rospy.get_param("save_dir")
        self.save_result_dir = os.path.join(self.pkg_dir, self.save_dir)
        self.timestamp = None


        self.ip = "220.90.239.142"
        self.port = 1883
        self.username = "robot"
        self.password = "robot123"
        self.robot_id = "geon_1"
        self.topic = f"mrm/{self.robot_id}/eventAI/result"
        self.api_url = f"http://{self.ip}:7080/col/v1/image/saveImageFiles.do"
        self.header_key = "X-GEO-ROADAI-API"
        self.header_value = "Geon ce79e749650fb0c8595801d94c222bbc"

        self.client = mqtt.Client()


    def __call__(self, *args, **kwds):
        self.recive_result()
        self.message_parser()
        self.configure_mqtt()
        result = self.upload_image()
        if result["status"] == "success":
            print(f"[성공] 응답: {result['response']}")
        else:
            print(f"[실패] 상태 코드: {result.get('code')} | 메시지: {result.get('message')}")
        
    def recive_result(self):
        if not self.results:
            print("No results to process.")
            return

        if not isinstance(self.results, list):
            print(f"Error: Expected a list but got {type(self.results)}")
            return
        
        for idx, obj in enumerate(self.results):
            if not isinstance(obj, dict):
                print(f"Invalid result at index {idx}: {obj}")
                continue

            try:
                self.timestamp = obj.get('Time', 'Unknown')
                self.img_name = obj.get('IMG_ID', 'Unknown')
                
                # Bounding Box 처리
                bounding_box = obj.get('BoundingBOX', None)
                if bounding_box and isinstance(bounding_box, (list, tuple)) and len(bounding_box) == 4:
                    x1, y1, x2, y2 = [str(coord) for coord in bounding_box]
                    self.boxes_result.append((f"{obj.get('ClassID', 'Unknown')}", f"{obj.get('Confidence', 0)}", x1, y1, x2, y2))
                else:
                    print(f"Invalid or missing Bounding Box in result[{idx}]: {bounding_box}")

                # Event 처리
                event = {
                    "eventID": obj.get('ID', 'Unknown'),
                    "eventType": "SOC",
                    "imageID": f"{obj.get('IMG_ID', 'Unknown')}.jpg",
                    "timestamp": obj.get('Time', 'Unknown'),
                    "location": {
                        "x": obj.get('Longitude', '0'),
                        "y": obj.get('Latitude', '0')
                    },
                    "eventContent": {
                        "track_id": "1",
                        "classified": obj.get('ClassID', 'Unknown'),
                        "score": obj.get('Confidence', 0)
                    }
                }
                self.events.append(event)
            except Exception as e:
                print(f"Error processing result[{idx}]: {e}")


    def message_parser(self):
        self.message = {
        "transactionId": str(uuid.uuid4()),
        "messageId": str(uuid.uuid4()),
        "robotId": self.robot_id,
        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "events": self.events
        }
    
    def configure_mqtt(self):
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.connect(self.ip, self.port, 60)
        self.client.loop_start()
        self.publish_message()
        self.client.loop_stop()


    # MQTT 연결 콜백 함수
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully")
        else:
            print(f"Connection failed with code {rc}")
    
    def publish_message(self):
        """
        MQTT 메시지를 발행합니다.

        Args:
            client (mqtt.Client): MQTT 클라이언트.
            topic (str): 메시지를 발행할 토픽.
            message (dict): 발행할 메시지 내용.
        """
        try:
            payload = json.dumps(self.message)
            result = self.client.publish(self.topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("Message published successfully")
            else:
                print(f"Failed to publish message with result code {result.rc}")
        except Exception as e:
            print(f"Failed to publish message: {e}")

    def upload_image(self):
        headers = {
            self.header_key: self.header_value
        }
        if not self.img_name:
            return {"status": "error", "message": "Image name is not set"}
        file_path = os.path.join(self.save_result_dir, f"{self.img_name}.jpg")
        try:
            with open(file_path, "rb") as image_file:
                files = {
                    "images": (f"{self.img_name}.jpg", image_file, "image/jpg"),
                }
                # ...
        except FileNotFoundError:
            return {"status": "error", "message": f"File not found: {file_path}"}

        data = {
            "box_result": self.boxes_result,
            "timestamp": self.timestamp
        }

        try:
            print(f"파일 업로드 중")
            print(f"Event ID: {self.img_name}")
            response = requests.post(self.api_url, headers=headers, files=files, data=data)
            print(f"응답 상태 코드: {response.status_code}")

            if response.status_code == 200:
                return {"status": "success", "response": response.text}
            else:
                return {"status": "failure", "code": response.status_code, "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}