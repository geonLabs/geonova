#!/usr/bin/env python3
import rospy
from geonova.msg import Detections, Detection
import math
import time

class DetectionFilter:
    def __init__(self):
        rospy.init_node("geonova_filter", anonymous=True)

        # 구독할 토픽 설정
        self.subscriber = rospy.Subscriber("/detections_topic", Detections, self.callback)

        # 중복 제거된 데이터를 발행할 토픽
        self.publisher = rospy.Publisher("/filtered_detections", Detections, queue_size=10)

        self.filtered_detections = []  # 중복 제거된 검출 객체 저장
        self.last_received_time = None  # 마지막으로 메시지를 받은 시간
        self.publish_interval = 10  # ✅ 10초 동안 데이터 수집 후 발행

    def gps_distance(self, lat1, lon1, lat2, lon2):
        """ 위도(lat), 경도(lon) 기준으로 두 지점 사이의 거리를 계산 (단위: 미터) """
        R = 6371000  # 지구 반지름 (m)
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  # 결과 단위: 미터 (m)

    def add_new_detections(self, new_detections):
        """ 중복 확인 후 새로운 데이터 추가 """
        for new_detection in new_detections:
            is_unique = True
            for existing in self.filtered_detections:
                distance = self.gps_distance(new_detection.object_lat, new_detection.object_lon,
                                             existing.object_lat, existing.object_lon)
                if distance < 1.0:  # 1m 이내면 중복으로 간주
                    is_unique = False
                    break
            
            if is_unique:
                self.filtered_detections.append(new_detection)  # ✅ 중복이 아니면 추가

    def publish_filtered_detections(self):
        """ 10초 동안 받은 데이터 중 중복을 제거한 데이터를 발행 (빈 메시지는 발행하지 않음) """
        if not self.filtered_detections:
            return  # ✅ 빈 메시지는 발행하지 않음

        filtered_msg = Detections()
        filtered_msg.detections = self.filtered_detections
        self.publisher.publish(filtered_msg)

        rospy.loginfo(f"Published {len(filtered_msg.detections)} filtered detections.")

        self.filtered_detections = []  # 🔥 발행 후 리스트 초기화
        self.last_received_time = None  # 타이머 리셋

    def callback(self, msg):
        """ 새로운 데이터를 계속 확인하면서 중복을 제거하고, 처음 데이터 수신 후 10초가 지나면 발행 """
        current_time = time.time()

        if self.last_received_time is None:
            self.last_received_time = current_time  # ✅ 첫 메시지가 들어온 시점부터 10초 시작

        self.add_new_detections(msg.detections)  # ✅ 들어오는 데이터 계속 확인

        if current_time - self.last_received_time >= self.publish_interval:
            self.publish_filtered_detections()  # 10초가 지나면 필터링된 데이터 발행

if __name__ == "__main__":
    try:
        detector = DetectionFilter()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
