import math

def calculate_new_gps(lat, lon, heading, distance, pixel_x, pixel_y, img_width=1920, img_height=1080, fov_x=128, fov_y=80):
    """
    현재 GPS 좌표(lat, lon)와 heading(방위각), 카메라 픽셀 좌표(pixel_x, pixel_y),
    그리고 물체까지의 거리(distance)를 이용해 물체의 실제 GPS 좌표를 계산한다.
    
    :param lat: 현재 GPS 위도 (degrees)
    :param lon: 현재 GPS 경도 (degrees)
    :param heading: 방위각 (degrees, 0~360, 0 = 북, 90 = 동, 180 = 남, 270 = 서)
    :param distance: 카메라로부터 측정된 물체까지의 거리 (float, meters)
    :param pixel_x: 물체의 화면 내 x 좌표 (0~1920 픽셀)
    :param pixel_y: 물체의 화면 내 y 좌표 (0~1080 픽셀)
    :param img_width: 카메라 해상도 가로 크기 (기본값 1920)
    :param img_height: 카메라 해상도 세로 크기 (기본값 1080)
    :param fov_x: 카메라의 가로 시야각 (기본값 128도)
    :param fov_y: 카메라의 세로 시야각 (기본값 80도)
    :return: 물체의 GPS 좌표 (위도, 경도)
    """
    # 지구 반지름 (미터)
    R = 6378137.0  
    37.6322606667, 126.793329
    # 각도를 라디안으로 변환
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    heading_rad = math.radians(heading)
    
    # 카메라 중심 기준으로 상대적 픽셀 위치 (-1 ~ 1 범위로 정규화)
    norm_x = (pixel_x - img_width / 2) / (img_width / 2)
    norm_y = (pixel_y - img_height / 2) / (img_height / 2)
    
    # 픽셀 위치를 실제 각도로 변환
    angle_x = math.radians(norm_x * (fov_x / 2))
    angle_y = math.radians(norm_y * (fov_y / 2))
    
    # 거리값을 이용해 실제 x, y 좌표 변환 (월드 좌표계)
    object_x = distance * math.tan(angle_x)
    object_y = distance * math.tan(angle_y)
    adjusted_distance = math.sqrt(distance**2 + object_x**2 + object_y**2)  # 거리 보정
    
    # 거리만큼 이동한 새로운 위도 계산
    new_lat_rad = math.asin(math.sin(lat_rad) * math.cos(adjusted_distance / R) +
                            math.cos(lat_rad) * math.sin(adjusted_distance / R) * math.cos(heading_rad))
    
    # 거리만큼 이동한 새로운 경도 계산
    new_lon_rad = lon_rad + math.atan2(math.sin(heading_rad) * math.sin(adjusted_distance / R) * math.cos(lat_rad),
                                       math.cos(adjusted_distance / R) - math.sin(lat_rad) * math.sin(new_lat_rad))
    
    # 라디안 값을 다시 도(degree)로 변환
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)
    
    return new_lat, new_lon

# 예제 실행
# current_lat = 37.6345921  # 현재 위도 (서울 예제)
# current_lon = 126.7902151  # 현재 경도

current_lat, current_lon = 37.6322824, 126.7932448

# 37.6345921, 126.7902151
heading = 137.07139128198276  # 북동쪽 (0~360도 제공)
object_distance = 5.231924861416211  # 100.0m (float, 미터 단위)

pixel_x = 452  # 화면 중앙 (1920x1080 기준)
pixel_y = 869  # 화면 중앙

object_gps = calculate_new_gps(current_lat, current_lon, heading, object_distance, pixel_x, pixel_y)
print("Object GPS Coordinates:", object_gps)
37.632238120569916, 126.79329680882941