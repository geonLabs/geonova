import math

def quaternion_to_euler(q):
    """
    쿼터니언(q)을 오일러 각(Roll, Pitch, Yaw)으로 변환하는 함수
    - 입력: q = [q0, q1, q2, q3] (사원수)
    - 출력: (roll, pitch, yaw) (라디안 단위)
    """
    q0, q1, q2, q3 = q

    # Roll (X축 회전)
    sinr_cosp = 2 * (q0 * q1 + q2 * q3)
    cosr_cosp = 1 - 2 * (q1 * q1 + q2 * q2)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (Y축 회전)
    sinp = 2 * (q0 * q2 - q3 * q1)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  # -90도 ~ 90도 제한
    else:
        pitch = math.asin(sinp)

    # Yaw (Z축 회전)
    siny_cosp = 2 * (q0 * q3 + q1 * q2)
    cosy_cosp = 1 - 2 * (q2 * q2 + q3 * q3)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw  # 결과는 라디안 값


def mahony_filter(angular_velocity, linear_acceleration, q,
                  dt=0.01, integral_fb=[0.0, 0.0, 0.0], Kp=2.0, Ki=0.00):
    """
    Mahony 필터: 자이로스코프 및 가속도계 데이터를 융합하여 자세(Orientation)를 추정하는 필터

    - angular_velocity: 자이로스코프 데이터 (각속도, rad/s) [gx, gy, gz]
    - linear_acceleration: 가속도계 데이터 (중력가속도 포함) [ax, ay, az]
    - q: 현재 쿼터니언 상태 [q0, q1, q2, q3]
    - dt: 샘플링 주기 (초) (기본값: 0.01초, 100Hz)
    - integral_fb: 적분 피드백 값 (오차 누적 보정용)
    - Kp: 비례 게인 (현재 오차에 대한 보정 속도)
    - Ki: 적분 게인 (드리프트 보정 강도)

    - 출력: (roll, pitch, yaw) (각도 단위)
    """

    # 가속도 벡터의 크기 계산 (정규화 필요)
    norm_accel = math.sqrt(sum(a ** 2 for a in linear_acceleration))
    if norm_accel == 0:
        return  # 가속도 데이터가 없으면 계산 불가 (0으로 나누기 방지)
    
    # 가속도 벡터 정규화
    accel = [a / norm_accel for a in linear_acceleration]

    # 중력 벡터의 방향을 현재 쿼터니언으로부터 계산
    vx = 2 * (q[1] * q[3] - q[0] * q[2])
    vy = 2 * (q[0] * q[1] + q[2] * q[3])
    vz = q[0] ** 2 - q[1] ** 2 - q[2] ** 2 + q[3] ** 2

    # 가속도계 기반 중력 방향과 예상 중력 방향의 차이(오차) 계산
    ex = accel[1] * vz - accel[2] * vy
    ey = accel[2] * vx - accel[0] * vz
    ez = accel[0] * vy - accel[1] * vx

    # 적분 보정 (오차 누적)
    integral_fb[0] += Ki * ex * dt
    integral_fb[1] += Ki * ey * dt
    integral_fb[2] += Ki * ez * dt

    # 보정된 각속도 계산 (비례 + 적분 보정 적용)
    gx = angular_velocity[0] + Kp * ex + integral_fb[0]
    gy = angular_velocity[1] + Kp * ey + integral_fb[1]
    gz = angular_velocity[2] + Kp * ez + integral_fb[2]

    # 쿼터니언 미분 계산 (Gyroscope 데이터를 기반으로 업데이트)
    q_dot = [
        -0.5 * (q[1] * gx + q[2] * gy + q[3] * gz),
        0.5 * (q[0] * gx + q[2] * gz - q[3] * gy),
        0.5 * (q[0] * gy - q[1] * gz + q[3] * gx),
        0.5 * (q[0] * gz + q[1] * gy - q[2] * gx)
    ]

    # 쿼터니언 업데이트
    q[0] += q_dot[0] * dt
    q[1] += q_dot[1] * dt
    q[2] += q_dot[2] * dt
    q[3] += q_dot[3] * dt

    # 쿼터니언 정규화 (단위 크기를 유지하여 안정성 확보)
    norm_q = math.sqrt(sum(qi ** 2 for qi in q))
    q[:] = [qi / norm_q for qi in q]  # 리스트 내부 값을 직접 변경하여 반영

    # 쿼터니언을 오일러 각으로 변환 (라디안)
    roll, pitch, yaw = quaternion_to_euler(q)

    # 결과를 도(degree) 단위로 변환하여 반환
    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)


# 예제 실행 (샘플 입력값)
if __name__ == "__main__":
    # 예제 입력값 (자이로스코프, 가속도계, 초기 쿼터니언)
    angular_velocity = [0.01, 0.02, 0.03]  # rad/s
    linear_acceleration = [0, 0, -9.81]  # m/s² (중력 방향)
    q = [1.0, 0.0, 0.0, 0.0]  # 초기 쿼터니언 (회전 없음)

    # Mahony 필터 실행
    roll, pitch, yaw = mahony_filter(angular_velocity, linear_acceleration, q)

    # 결과 출력
    print(f"Roll: {roll:.2f}°, Pitch: {pitch:.2f}°, Yaw: {yaw:.2f}°")
