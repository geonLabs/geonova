import rospy
import math
from sensor_msgs.msg import NavSatFix, Imu
from geometry_msgs.msg import Quaternion
from time import time

class GPSIMUInitializer:
    def __init__(self):
        rospy.init_node("gps_imu_initializer")

        # ROS 토픽 구독
        rospy.Subscriber("/fix", NavSatFix, self.gps_callback)
        rospy.Subscriber("/imu/data", Imu, self.imu_callback)

        # GPS 데이터 저장
        self.last_gps = None
        self.current_gps = None

        # IMU 초기화 상태
        self.imu_initialized = False

        # 신뢰 가능한 GPS 여부
        self.gps_reliable = False

        # GPS 신뢰성 기준 (예: HDOP 값)
        self.hdop_threshold = 10.0  # HDOP가 이 값 이하일 때 신뢰 가능

        # 현재 IMU 방향
        self.current_heading = None

        # 마지막 초기화 시간
        self.last_initialization_time = time()
        self.initialization_interval = 5  # 5초마다 초기화

        rospy.loginfo("GPS-IMU Initializer Node Started")

    def gps_callback(self, msg):
        # GPS 신뢰성 평가
        if msg.status.status >= 0 and msg.position_covariance[0] <= self.hdop_threshold:
            self.gps_reliable = True
        else:
            self.gps_reliable = False

        # GPS 데이터 저장
        self.last_gps = self.current_gps
        self.current_gps = (msg.latitude, msg.longitude)

        # 5초마다 초기화
        current_time = time()
        if self.gps_reliable and self.last_gps and (current_time - self.last_initialization_time >= self.initialization_interval):
            self.initialize_imu_orientation()
            self.last_initialization_time = current_time

    def imu_callback(self, msg):
        # IMU 데이터를 활용할 준비
        if self.imu_initialized:
            # Yaw 업데이트 (현재 Orientation 출력)
            quaternion = msg.orientation
            yaw = self.quaternion_to_yaw(quaternion)
            self.current_heading = yaw
            rospy.loginfo(f"Updated IMU Heading: {yaw:.2f} degrees")
        else:
            rospy.loginfo("Waiting for GPS initialization to complete.")

    def calculate_heading(self, lat1, lon1, lat2, lon2):
        """ GPS 두 점 간의 방위각 계산 """
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        d_lon = lon2 - lon1
        x = math.sin(d_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)

        heading = math.atan2(x, y)  # 라디안 단위
        heading = math.degrees(heading)  # 각도로 변환
        heading = (heading + 360) % 360  # 음수 값을 0-360도로 변환
        return heading

    def yaw_to_quaternion(self, yaw):
        """ Yaw 값을 쿼터니언으로 변환 """
        yaw_rad = math.radians(yaw)
        w = math.cos(yaw_rad / 2)
        x = 0
        y = 0
        z = math.sin(yaw_rad / 2)
        return Quaternion(w=w, x=x, y=y, z=z)

    def quaternion_to_yaw(self, quaternion):
        """ 쿼터니언에서 Yaw 값을 추출 """
        w = quaternion.w
        x = quaternion.x
        y = quaternion.y
        z = quaternion.z

        # Yaw 계산 (Z 축 회전)
        yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
        yaw = math.degrees(yaw)  # 각도로 변환
        return (yaw + 360) % 360  # 0-360도로 변환

    def initialize_imu_orientation(self):
        """ GPS 데이터를 기반으로 IMU 초기 방향 보정 """
        if self.last_gps and self.current_gps:
            lat1, lon1 = self.last_gps
            lat2, lon2 = self.current_gps

            # GPS를 이용해 방위각 계산
            heading = self.calculate_heading(lat1, lon1, lat2, lon2)
            rospy.loginfo(f"Calculated Heading: {heading:.2f} degrees")

            # 방위각을 쿼터니언으로 변환
            orientation = self.yaw_to_quaternion(heading)
            rospy.loginfo(f"IMU Orientation Initialized: {orientation}")

            # IMU 초기화 완료 플래그 설정
            self.imu_initialized = True
            self.current_heading = heading
        else:
            rospy.logwarn("Insufficient GPS data to initialize orientation.")

    def run(self):
        rospy.spin()

if __name__ == "__main__":
    initializer = GPSIMUInitializer()
    initializer.run()

