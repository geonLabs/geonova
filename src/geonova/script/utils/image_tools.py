import sys
sys.path.append("/usr/lib/python3/dist-packages")  # Ensure VPI is accessible
import vpi

import cv2
import numpy as np
import torch
from torch.nn.functional import interpolate
from cv_bridge import CvBridge
import rospy
import time

class image_tools:
    def __init__(self):
        self.bridge = CvBridge()

    def convert_image(self, image_msg):
        try:
            if image_msg.encoding == "16UC1":
                # Convert depth image to a CV2-compatible format
                cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding="passthrough")
            elif image_msg.encoding == "bgr8":
                # Convert color image
                cv_image = self.bridge.imgmsg_to_cv2(image_msg, desired_encoding="bgr8")
            else:
                rospy.logerr(f"Unsupported image encoding: {image_msg.encoding}")
                return None
            return cv_image
        except Exception as e:
            rospy.logerr(f"Failed to convert image: {e}")
            return None

    def resize_with_padding(self, image, target_size=(640, 640), device="cuda"):
        """
        Resize the image to the target size with padding to maintain aspect ratio.
        This function performs resizing on GPU using PyTorch if a CUDA device is specified.

        Args:
            image (numpy.ndarray): Input image.
            target_size (tuple): Target size (width, height).
            device (str): Device to perform the operations ("cpu" or "cuda").

        Returns:
            torch.Tensor: Resized and padded image as a Torch tensor on the specified device,
                          formatted for YOLOv8 input (B, C, H, W) with values in the range [0, 1].
        """
        start_time = time.time()
        original_height, original_width = image.shape[:2]
        target_width, target_height = target_size

        # Convert image to Torch tensor and move to the specified device
        tensor_image = torch.from_numpy(image).permute(2, 0, 1).float().to(device) / 255.0

        # Calculate the scaling factor to fit the image within the target size
        scale = min(target_width / original_width, target_height / original_height)

        # Calculate the new width and height
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # Resize the image using PyTorch interpolate
        resized_image = interpolate(
            tensor_image.unsqueeze(0), 
            size=(new_height, new_width), 
            mode="bilinear", 
            align_corners=False
        ).squeeze(0)

        # Calculate padding values
        pad_width = target_width - new_width
        pad_height = target_height - new_height

        top = pad_height // 2
        bottom = pad_height - top
        left = pad_width // 2
        right = pad_width - left

        # Add padding using torch.nn.functional.pad
        padded_image = torch.nn.functional.pad(
            resized_image, (left, right, top, bottom), mode="constant", value=0
        )

        # Add batch dimension for YOLOv8 input (B, C, H, W)
        yolo_input = padded_image.unsqueeze(0)
        end_time = time.time()
        rospy.loginfo(f"Resize and padding processing time: {(end_time - start_time) * 1000:.2f} ms")
        return yolo_input

    def ros_image_to_numpy(self, camera_image_msg):
        if camera_image_msg.encoding == "rgb8":
            dtype = np.uint8
            channels = 3
            print("using rgb8")
        elif camera_image_msg.encoding == "bgr8":
            dtype = np.uint8
            channels = 3
            # print("using bgr8")/
        elif camera_image_msg.encoding == "mono8":
            dtype = np.uint8
            channels = 1
            print("using mono8")
        elif camera_image_msg.encoding == "16UC1":
            dtype = np.uint16
            channels = 1
            print("using 16UC1")
        else:
            raise ValueError(f"지원되지 않는 인코딩 형식: {camera_image_msg.encoding}")

        # ROS Image 메시지를 1차원 배열로 변환
        image_data = np.frombuffer(camera_image_msg.data, dtype=dtype)

        # 1차원 배열을 3차원 배열로 재구성
        img_np_array = image_data.reshape((camera_image_msg.height, camera_image_msg.width, channels))

        return img_np_array

    def numpy_to_vpi_image(self, img_np_array):
        if not img_np_array.flags.writeable:
            img_np_array = np.copy(img_np_array)
        img_np_array.setflags(write=True)
        return vpi.asimage(img_np_array)

    def flip_img(self, vpi_img):
        with vpi.Backend.CUDA:
            return vpi_img.image_flip(vpi.Flip.BOTH)


    def add_padding_to_original(self, vpi_image, target_width, target_height):
        original_width, original_height = vpi_image.size
        # 스케일 비율 계산
        scale_x = target_width / original_width
        scale_y = target_height / original_height
        scale = min(scale_x, scale_y)

        # 새로운 크기 계산
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # 패딩 크기 계산
        pad_left = (target_width - new_width) // 2
        pad_top = (target_height - new_height) // 2

        backend = vpi.Backend.CUDA

        with backend:
            # NV12_ER 형식으로 변환
            nv12_image = vpi_image.convert(vpi.Format.NV12_ER, backend=backend)

            # 리스케일된 이미지를 저장할 임시 VPI 이미지 생성
            resized_nv12_image = vpi.Image((new_width, new_height), format=vpi.Format.NV12_ER)
            # 최종 출력 VPI 이미지 생성
            output_nv12_image = vpi.Image((target_width, target_height), format=vpi.Format.NV12_ER)

            # 리스케일 작업
            nv12_image.rescale(resized_nv12_image, interp=vpi.Interp.CATMULL_ROM, backend=backend)

            # 출력 이미지 초기화
            with output_nv12_image.wlock_cpu() as dst_data:
                y_data, uv_data = dst_data  # Y 성분과 UV 성분을 개별적으로 분리
                y_data.fill(0)  # Y 성분 초기화
                uv_data.fill(128)  # UV 성분 초기화 (중립색)

            # 리스케일된 이미지를 중앙에 배치
            with resized_nv12_image.rlock_cpu() as src_data:
                src_y_data, src_uv_data = src_data  # 리스케일된 Y/UV 성분 분리
                y_data[pad_top:pad_top+new_height, pad_left:pad_left+new_width] = src_y_data
                uv_data[pad_top//2:(pad_top+new_height)//2, pad_left//2:(pad_left+new_width)//2] = src_uv_data

            # NV12_ER 이미지를 원래 포맷으로 변환
            output_vpi_image = output_nv12_image.convert(vpi.Format.RGB8, backend=backend)

        return output_vpi_image

    def vpi_to_torch_tensor(self, rescaling_img):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        with rescaling_img.rlock_cuda() as cuda_buffer:
            torch_tensor = torch.as_tensor(cuda_buffer, device=device)
            torch_tensor = torch_tensor.permute(2, 0, 1).unsqueeze(0)
            torch_tensor = torch_tensor.float() / 255.0

        return torch_tensor