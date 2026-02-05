import depthai as dai

with dai.Device() as device:
    print("=== Device Info ===")
    print("MxId:", device.getMxId())
    print("Connected cameras:", device.getConnectedCameras())

    # 카메라 피처(이름/소켓/해상도 등) 확인
    feats = device.getCameraFeatures()
    print("\n=== Camera Features ===")
    for f in feats:
        print(
            "socket=", f.socket,
            "name=", f.name,
            "sensorName=", getattr(f, "sensorName", None),
        )

