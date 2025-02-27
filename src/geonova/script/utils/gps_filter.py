#!/usr/bin/env python3
import rospy
from geonova.msg import Detections, Detection
import math
import time
from collections import defaultdict
from utils.mqtt_send_v2 import PayloadSender  # ✅ PayloadSender 가져오기

class DetectionFilter:
    def __init__(self):
        rospy.init_node("geonova_filter", anonymous=True)

        # 토픽 구독
        self.subscriber = rospy.Subscriber("/detections_topic", Detections, self.callback)

        # 이미지별로 따로 저장하는 대신, 모든 검출을 (img_path, detection) 튜플로 저장
        self.all_detections = []
        self.last_received_time = None  # 첫 메시지 수신 시각 저장
        self.publish_interval = 10       # 10초 동안 데이터 수집 후 필터링 및 전송
        self.detection_radius = 3.0      # 반경 2m 이내 중복 (단위: m)

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Haversine 공식으로 두 지점 사이의 거리를 계산 (단위: m)"""
        R = 6371000  # 지구 반지름 (m)
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def filter_detections(self):
        """글로벌하게 수집된 검출 객체들 중 중복(같은 클래스 & 위치 반경 2m 내)을 제거"""
        if not self.all_detections:
            rospy.loginfo("🚫 저장할 검출 데이터 없음.")
            return

        rospy.loginfo(f"📢 총 {len(self.all_detections)}개의 검출 객체를 필터링 중...")

        unique_detections = []  # (img_path, detection) 튜플을 저장

        for img_path, detection in self.all_detections:
            duplicate_found = False
            for idx, (uniq_img_path, uniq_det) in enumerate(unique_detections):
                if detection.classid == uniq_det.classid:
                    distance = self.haversine_distance(
                        detection.object_lat, detection.object_lon,
                        uniq_det.object_lat, uniq_det.object_lon
                    )
                    # 중복 기준: 같은 클래스이고 반경 2m 이내 (경계 포함)
                    if distance <= self.detection_radius:
                        # 더 높은 신뢰도(confidence)를 가진 검출을 선택
                        if detection.conf > uniq_det.conf:
                            unique_detections[idx] = (img_path, detection)
                        duplicate_found = True
                        break
            if not duplicate_found:
                unique_detections.append((img_path, detection))

        # 이미지별로 그룹화: 각 이미지에 해당하는 검출 객체들을 모음
        filtered_by_image = defaultdict(list)
        for img_path, detection in unique_detections:
            filtered_by_image[img_path].append(detection)

        # 필터링된 총 검출 개수 로깅
        total_filtered = sum(len(dets) for dets in filtered_by_image.values())
        rospy.loginfo(f"✅ 필터링 후 총 {total_filtered}개의 검출 객체가 다음 로직으로 전송됩니다.")

        # 필터링 완료된 데이터 전송
        for img_path, detections in filtered_by_image.items():
            converted_data = self.convert_to_payload_format(detections)
            payload_sender = PayloadSender(converted_data, img_path)  # ✅ 이미지별로 전송
            payload_sender()  # ✅ 실행

        # 데이터 초기화
        self.all_detections.clear()
        self.last_received_time = None

    def callback(self, msg):
        """메시지를 수신하며 10초 동안 검출 객체들을 누적하고,
        10초 경과 시 중복 필터링 및 전송 수행"""
        current_time = time.time()

        if self.last_received_time is None:
            self.last_received_time = current_time  # 첫 메시지 수신 시각 저장

        # 각 메시지에서 모든 검출 객체를 (img_path, detection) 튜플 형태로 저장
        for detection in msg.detections:
            self.all_detections.append((msg.img_path, detection))

        if current_time - self.last_received_time >= self.publish_interval:
            self.filter_detections()

    def convert_to_payload_format(self, detections):
        """PayloadSender가 기대하는 리스트 형식으로 변환"""
        converted_data = []
        for detection in detections:
            converted_data.append([
                detection.classid,      # class_id (int)
                detection.conf,         # confidence (float)
                detection.x1,           # x1 (int)
                detection.y1,           # y1 (int)
                detection.x2,           # x2 (int)
                detection.y2,           # y2 (int)
                detection.object_lat,   # object_lat (float)
                detection.object_lon    # object_lon (float)
            ])
        return converted_data

if __name__ == "__main__":
    try:
        detector = DetectionFilter()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
