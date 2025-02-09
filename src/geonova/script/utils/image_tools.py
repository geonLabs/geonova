import os
import cv2
import uuid
import numpy as np
from cv_bridge import CvBridge
import rospy

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

            # Rotate the image 180 degrees
            #cv_image = cv2.rotate(cv_image, cv2.ROTATE_180)
            
            return cv_image
        except Exception as e:
            rospy.logerr(f"Failed to convert image: {e}")
            return None

    def save_image(self, cv_image, save_path):
        try:
            # 디렉토리가 없는 경우 생성
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            # UUID 기반 파일 이름 생성
            unique_filename = f"{uuid.uuid4()}.jpg"
            save_path = os.path.join(save_path, unique_filename)

            # 이미지 저장
            cv2.imwrite(save_path, cv_image)
            rospy.loginfo(f"Image saved to {save_path}")
        except Exception as e:
            rospy.logerr(f"Failed to save image: {e}")

    
    def calculate_depth_at_center(self, depth_image, center_x, center_y, box_width, box_height):
        """
        박스 내부의 깊이값을 계산합니다.

        :param depth_image: NumPy 배열로 된 깊이 이미지
        :param center_x: 중심 x 좌표 (픽셀 단위)
        :param center_y: 중심 y 좌표 (픽셀 단위)
        :param box_width: 박스의 너비 (픽셀 단위)
        :param box_height: 박스의 높이 (픽셀 단위)
        :return: 박스 내부 유효 깊이값의 평균 (미터 단위) 또는 None
        """
        height, width = depth_image.shape

        # 박스 좌표 계산
        top_left_x = max(center_x - box_width // 2, 0)
        top_left_y = max(center_y - box_height // 2, 0)
        bottom_right_x = min(center_x + box_width // 2, width)
        bottom_right_y = min(center_y + box_height // 2, height)

        # 박스 내 깊이값 추출
        box_depth_values = depth_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x].flatten()

        # print(box_depth_values)

        # 유효한 깊이값 필터링 (0 < depth <= 15미터)
        box_depth_values_m = 468.22 * 7.5 / box_depth_values   # cm → m
        valid_depths = box_depth_values_m[(box_depth_values_m > 0) & (box_depth_values_m <= 15.0)]

        if valid_depths.size == 0:
            return None

        # 이상치 제거 (상위 20% 제거)
        threshold = np.percentile(valid_depths, 80)
        filtered_depths = valid_depths[valid_depths <= threshold]

        if filtered_depths.size == 0:
            return None

        # 평균값 계산
        return np.mean(filtered_depths)
    
    def result_depth(self, depth_img, result):
        boxes = result.boxes.xywhn.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)
        confidences = result.boxes.conf.cpu().numpy()  

        height, width = depth_img.shape
        results = []
        
        for box, class_id, confidence in zip(boxes, class_ids, confidences):
            # 박스 좌표 (정규화된 값 → 픽셀 단위)
            center_x = int(box[0] * width)
            center_y = int(box[1] * height)
            box_width = int(box[2] * width)
            box_height = int(box[3] * height)
            
            # 깊이값 추출
            mean_depth_m = self.calculate_depth_at_center(depth_img, center_x, center_y, box_width, box_height)
            results.append((class_id, mean_depth_m, confidence, box[0], box[1], box[2], box[3]))
            print(mean_depth_m)
        return results
    
    def save_label_data(self, result):
        result_list = []

        
        pass
