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
            # 박스 좌표값(정수) 변환 및 score(실수) 값 유지
            box_values = ",".join(
            str(int(value)) if i in [2, 3, 4, 5] else f"{value:.2f}" if i == 1 else str(value)
            for i, value in enumerate(data[:6])
            )

            if self.boxes_result:
                self.boxes_result = f"{self.boxes_result},{box_values}"  # 기존 값에 공백으로 추가
            else:
                self.boxes_result = box_values  # 첫 번째 박스

            x = data[7]
            y = data[6]

            evnet = {
                "eventID": str(uuid.uuid4()),
                "eventType": "SOC",
                "imageID": os.path.basename(self.img_path),
                "timestamp": self.timestamp,
                "location": {
                    "x": str(x),
                    "y": str(y),
                },
                "eventContent": {
                    "track_id": "1",
                    "classified": str(data[0]),  # classified는 그대로 문자열
                    "score": str(data[1])  # score는 그대로 문자열
                }
            }
            self.events.append(evnet)

    def message_parser(self):
        self.message = {
        "transactionId": f"{uuid.uuid4()}",
        "messageId": f"{uuid.uuid4()}",
        "robotId": self.robot_id,
        "timestamp": datetime.now().strftime("%Y%m%d%H%M%S"),
        "events": self.events
        }


    # MQTT 연결 콜백 함수
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
                pass
            else:
                print(f"Failed to publish message with result code {result.rc}")
        except Exception as e:
            print(f"Failed to publish message: {e}")




    def upload_image(self):
        headers = {
            self.header_key: self.header_value
        }
        if not self.img_path:
            return {"status": "error", "message": "Image name is not set"}
        try:
            # 파일 열기
            with open(self.img_path, "rb") as image_file:
                files = {
                    "images": (f"{os.path.basename(self.img_path)}", image_file, "image/jpg"),
                }
                # print(self.boxes_result)
                # 데이터 구성
                data = {
                    "box_result": self.boxes_result,
                    "timestamp": self.timestamp
                }

                # 요청 전송
                print(f"파일 업로드 중")
                response = requests.post(self.api_url, headers=headers, files=files, data=data)
                print(f"응답 상태 코드: {response.status_code}")

                if response.status_code == 200:
                    return {"status": "success", "response": response.text}
                else:
                    return {"status": "failure", "code": response.status_code, "message": response.text}
        except FileNotFoundError:
            return {"status": "error", "message": f"File not found: {self.img_path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}