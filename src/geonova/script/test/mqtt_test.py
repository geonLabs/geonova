import uuid
from datetime import datetime
from lee_mqtt import PayloadSender


def create_sample_results():
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    image_uuid = "6821af1c-9f11-4804-bca8-0a2859d9ca9e"
    event_uuid = str(uuid.uuid4())

    results = [
        {
            # ===== event =====
            "ID": image_uuid,                 # eventID
            "Time": now,                      # timestamp
            "ClassID": "201",                 # classified
            "Confidence": "0.3393899325291668",  # ✅ 문자열
            
            # ===== location =====
            "Latitude": 36.554039,
            "Longitude": 127.277328,

            # ===== image =====
            "IMG_ID": image_uuid,             # imageID (확장자는 Sender에서 붙임)

            # ===== bounding box (필수 필드라 더미라도 넣음) =====
            "BoundingBOX": [100, 150, 300, 400],

            # ===== 기타 PayloadSender 요구 필드 =====
            "GPS_Lat": 36.554039,
            "GPS_Long": 127.277328,
            "Heading": 0.0,
            "Depth": 0.0,
            "Count": 1
        }
    ]

    return results, image_uuid


if __name__ == "__main__":
    IMAGE_PATH = "/home/jm/workspace/KT_Project/new_geon_ws/src/geonova/save_dir/2026-01-30"   # 실제 이미지 경로

    results, image_uuid = create_sample_results()

    print(f"전송 이미지: {IMAGE_PATH}/{image_uuid}.jpg")

    sender = PayloadSender(
        results=results,
        img_path=IMAGE_PATH
    )

    sender()
