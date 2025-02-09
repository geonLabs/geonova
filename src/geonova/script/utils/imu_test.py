import serial
import numpy as np
import time
from scipy.spatial.transform import Rotation as R

# 지구 반지름 (km)
EARTH_RADIUS = 6371.0

# 초기 GPS 좌표
initial_lat = 37.7749  # degrees
initial_lon = -122.4194  # degrees

# 시리얼 포트 설정
serial_port = "/dev/ttyUSB0"
baudrate = 921600

# 시리얼 포트 열기
ser = serial.Serial(serial_port, baudrate, timeout=1)
time.sleep(2)  # 포트 안정화 대기

# 전역 변수 초기화 (global 제거)
prev_velocity = 0.0
dt = 0.001  # IMU 1ms(1000Hz) 업데이트 반영
prev_heading = None  # 초기 방향
cumulative_rotation = 0.0  # 누적 회전 각도 (원형 궤적 판단)

def read_serial_data():
    """ 시리얼 데이터 읽기 및 파싱 """
    line = ser.readline().decode("utf-8").strip()
    
    if not line.startswith("*"):
        return None

    try:
        # '*' 제거 후 데이터 파싱
        raw_data = line[1:].split(",")

        if len(raw_data) < 13:
            print("데이터 개수 부족:", raw_data)
            return None

        # Quaternion (z, y, x, w)
        qz, qy, qx, qw = map(float, raw_data[0:4])

        # Gyroscope (x, y, z) in rad/s
        gyro_x, gyro_y, gyro_z = map(float, raw_data[4:7])

        # Accelerometer (x, y, z) in m/s^2
        acc_x, acc_y, acc_z = map(float, raw_data[7:10])

        # Magnetometer (x, y, z) in μT
        mag_x, mag_y, mag_z = map(float, raw_data[10:13])

        return {
            "quaternion": (qx, qy, qz, qw),
            "gyro": (gyro_x, gyro_y, gyro_z),
            "accel": (acc_x, acc_y, acc_z),
            "magnet": (mag_x, mag_y, mag_z)
        }
    
    except Exception as e:
        print("Parsing Error:", e)
        return None


def quaternion_to_heading(qx, qy, qz, qw):
    """ Quaternion → Euler 변환 후 Yaw 값 (Heading) 반환 """
    r = R.from_quat([qx, qy, qz, qw])
    euler = r.as_euler('xyz', degrees=True)  # (roll, pitch, yaw)
    yaw = euler[2]  # Yaw 값 (방위각)
    return np.radians(yaw)  # 라디안 변환


def update_position(initial_lat, initial_lon, heading, velocity, dt=0.001):
    """ 속도 및 방위각을 이용하여 GPS 위치 업데이트 """
    distance = velocity * dt  # 거리 = 속도 * 시간
    
    # 위도, 경도 변화량 계산
    delta_lat = (distance * np.cos(heading)) / EARTH_RADIUS
    delta_lon = (distance * np.sin(heading)) / (EARTH_RADIUS * np.cos(np.radians(initial_lat)))

    # 새로운 GPS 좌표 반환
    new_lat = initial_lat + np.degrees(delta_lat)
    new_lon = initial_lon + np.degrees(delta_lon)
    
    return new_lat, new_lon


def process_imu_data(sensor_data, prev_heading, cumulative_rotation, prev_velocity):
    """ IMU 데이터를 처리하고 속도를 갱신하며 U턴 및 원형 경로 감지 """
    # Quaternion → Heading 변환
    heading = quaternion_to_heading(*sensor_data["quaternion"])

    # 자이로스코프 데이터 활용
    gyro_z = sensor_data["gyro"][2]  # z축 회전 속도 (rad/s)

    # U턴 감지 (이전 heading과 현재 heading 비교)
    if prev_heading is not None:
        heading_change = np.degrees(abs(heading - prev_heading))

        if heading_change > 150:
            print("U턴 감지")

    # 원형 회전 감지 (자이로스코프 적분)
    cumulative_rotation += np.degrees(gyro_z) * dt  # rad → degrees 변환

    if abs(cumulative_rotation) >= 360:
        print("원형 궤적 감지")
        cumulative_rotation = 0  # 리셋

    # 가속도를 이용하여 속도 갱신
    acc_x, acc_y, acc_z = sensor_data["accel"]
    acc_z -= 9.81  # 중력 보정
    accel_magnitude = np.linalg.norm([acc_x, acc_y])  # XY 평면 속도 계산

    # 속도 변화 적용 (단순 적분)
    velocity = prev_velocity + accel_magnitude * dt  

    # 마찰력 적용 (속도 감속)
    velocity *= 0.999  # 감속 계수 적용 (1ms 기준)

    # 너무 작은 속도는 0으로 설정
    if velocity < 0.01:
        velocity = 0

    # 이동 속도 제한 (과도한 속도 증가 방지)
    velocity = min(velocity, 2.5)  # 최대 2.5 m/s 제한

    return heading, cumulative_rotation, velocity


# 주 실행 루프
try:
    while True:
        sensor_data = read_serial_data()
        if sensor_data:
            # IMU 데이터 처리 및 속도 갱신
            prev_heading, cumulative_rotation, prev_velocity = process_imu_data(
                sensor_data, prev_heading, cumulative_rotation, prev_velocity
            )

            # 위치 업데이트
            initial_lat, initial_lon = update_position(initial_lat, initial_lon, prev_heading, prev_velocity, dt)

            # 결과 출력
            print(f"Updated GPS: Lat {initial_lat:.6f}, Lon {initial_lon:.6f}, Velocity: {prev_velocity:.4f} m/s")

        time.sleep(dt)

except KeyboardInterrupt:
    print("Stopping...")
    ser.close()
