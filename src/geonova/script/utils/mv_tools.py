import rospy
import math

class CalCoordinate:
    def __init__(self, imu_msg, gps_msg, depth_result, heading_msg):
    # def __init__(self, imu_msg, gps_msg, depth_result):
        self.lat = gps_msg.latitude
        self.lon = gps_msg.longitude

        self.heading = heading_msg.quaternion.w

        self.imu_orient = imu_msg.orientation
        self.imu_ang = imu_msg.angular_velocity
        self.imu_acc = imu_msg.linear_acceleration

        self.rgb_width = rospy.get_param("rgb_width", 1920)
        self.rgb_height = rospy.get_param("rgb_height", 1920)
        self.rgb_fov_h = rospy.get_param("rgb_fov_h", 95)
        self.rgb_fov_v = rospy.get_param("rgb_fov_v", 74)

        self.depth_result = depth_result # [(result1), (result2), ...]

        self.obj_results = []

    def __call__(self, *args, **kwds):
        if self.depth_result is None:
            return
        self.gps_coordinate()
        if len(self.return_result()) == 0:
            return None
        return self.return_result()

    def gps_coordinate(self):
        R = 6378137.0  # 지구 반지름 (미터)

        # 위도, 경도, heading을 라디안으로 변환
        lat_rad = cal_radians(self.lat)
        lon_rad = cal_radians(self.lon)
        heading_rad = cal_radians(self.heading)

        for result in self.depth_result:
            norm_x = (result[3] - self.rgb_width / 2) / (self.rgb_width / 2)

            # 좌우 각도 (라디안)
            angle_x = cal_radians(norm_x * (self.rgb_fov_h / 2))
            
            # 카메라 optical axis에 대한 좌우 오프셋 (미터)
            object_x = result[1] * math.tan(angle_x)
            
            # 수평 거리: optical depth와 좌우 오프셋만 고려 (수직 성분은 배제)
            # d = sqrt((result[1])^2 + (object_x)^2) = result[1] / cos(angle_x)
            horizontal_distance = result[1] / math.cos(angle_x)
            
            # 진행방향에 좌우 오프셋에 따른 보정각을 반영 (대략 angle_x와 동일)
            # (atan2(object_x, result[1]) == angle_x, 단 result[1] > 0 인 경우)
            delta_angle = math.atan2(object_x, result[1])
            effective_heading = heading_rad + delta_angle

            # 구면 좌표 공식 (대원거리 공식) 사용
            result_lat_rad = math.asin(math.sin(lat_rad) * math.cos(horizontal_distance / R) +
                                    math.cos(lat_rad) * math.sin(horizontal_distance / R) * math.cos(effective_heading))
            
            result_lon_rad = lon_rad + math.atan2(math.sin(effective_heading) * math.sin(horizontal_distance / R) * math.cos(lat_rad),
                                                math.cos(horizontal_distance / R) - math.sin(lat_rad) * math.sin(result_lat_rad))
            
            # 라디안을 다시 도(degree)로 변환
            object_lat = math.degrees(result_lat_rad)
            object_lon = math.degrees(result_lon_rad)

            self.obj_results.append([object_lat, object_lon])
        
        return self.obj_results

    def imu_coordinate(self):
        pass
    
    def return_gps_heading(self):
        return self.heading
    
    def return_result(self):
        send_mqtt_result = []
        """
        massage_protocol
        [class_id, confidence, x_center, y_center, width, height, object_lat, object_lon], 
        [], 
        [], ...
        """
        for i, obj_result in enumerate(self.obj_results):
            if self.depth_result[i][0] > 5:
                continue
            send_mqtt_result.append(
                (self.depth_result[i][0], 
                 self.depth_result[i][2],
                 self.depth_result[i][3],
                 self.depth_result[i][4], 
                 self.depth_result[i][5],
                 self.depth_result[i][6],
                 round(obj_result[0], 5), 
                 round(obj_result[1], 5)
                 )
            )

        return send_mqtt_result


class Moving_check:
    def __init__(self):
        pass
    
    def __call__(self, *args, **kwds):
        pass

def cal_radians(value):
    return math.radians(value)