import os
import cv2
import uuid
import numpy as np
from cv_bridge import CvBridge
import rospy
from datetime import datetime
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
                #cv_image = self.preprocess_color_image(cv_image)

            else:
                rospy.logerr(f"Unsupported image encoding: {image_msg.encoding}")
                return None

            # Rotate the image 180 degrees
            cv_image = cv2.rotate(cv_image, cv2.ROTATE_180)
            
            return cv_image
        except Exception as e:
            rospy.logerr(f"Failed to convert image: {e}")
            return None
    def preprocess_color_image(self, image, clahe_clip=2.0, clahe_tile=(2, 2), 
                           sobel_kernel=1, blend_ratio=(0.95, 0.05)):
        #start_time = time.time()
        # BGR 이미지를 LAB 색공간으로 변환
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        L, A, B = cv2.split(lab)
        
        # L 채널에 CLAHE 적용
        clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_tile)
        L_clahe = clahe.apply(L)
        
        # L 채널에 Sobel Edge Detection 적용
        grad_x = cv2.Sobel(L, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
        grad_y = cv2.Sobel(L, cv2.CV_64F, 0, 1, ksize=sobel_kernel)
        sobel_L = cv2.magnitude(grad_x, grad_y)
        sobel_L = cv2.convertScaleAbs(sobel_L)
        
        # CLAHE 결과와 Sobel 결과를 지정된 비율로 합성
        L_combined = cv2.addWeighted(L_clahe, blend_ratio[0], sobel_L, blend_ratio[1], 0)
        
        # 합성된 L 채널과 원래의 A, B 채널을 병합하여 LAB 이미지 재구성
        lab_combined = cv2.merge([L_combined, A, B])
        # LAB 이미지를 다시 BGR로 변환
        result = cv2.cvtColor(lab_combined, cv2.COLOR_LAB2BGR)
        
        # 전처리 후 결과에 gamma correction 적용
        result = self.adjust_gamma(result, gamma=1.2)
        
        #print(f"🕒 소요 시간: {time.time() - start_time:.2f}초")
        return result

    def adjust_gamma(self, image, gamma=1.2):
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255
                        for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(image, table)
    
    def save_image(self, cv_image, base_save_path, results):
        try:
            today_date = datetime.today().strftime('%Y-%m-%d')
            save_path = os.path.join(base_save_path, today_date)

            os.makedirs(save_path, exist_ok=True)

            unique_filename = f"{uuid.uuid4()}.jpg"
            full_save_path = os.path.join(save_path, unique_filename)

            de_identified_image, has_class_5_below_with_high_conf = self.de_identification(cv_image.copy(), results)

            # 클래스 5 이하에서 신뢰도 0.75 이상이 하나도 없으면 저장하지 않음
            if not has_class_5_below_with_high_conf:
                return None

            cv2.imwrite(full_save_path, de_identified_image)
            return full_save_path

        except Exception as e:
            rospy.logerr(f"Failed to save image: {e}")

    def de_identification(self, image, results):
        boxes = results.boxes.xyxy.cpu().numpy()
        class_ids = results.boxes.cls.cpu().numpy().astype(int)
        confidences = results.boxes.conf.cpu().numpy()

        height, width, _ = image.shape
        has_class_5_below_with_high_conf = False  # 클래스 5 이하에서 conf ≥ 0.75 여부 체크

        for box, class_id, confidence in zip(boxes, class_ids, confidences):
            # 클래스 5 이하 & conf_score ≥ 0.75 → 아무 처리 안 함 (체크만 함)
            if class_id <= 5 and confidence >= 0.8:
                has_class_5_below_with_high_conf = True
                continue

            # 클래스 6 이상 & conf_score ≥ 0.6 → 블러 적용
            if class_id >= 6 and confidence >= 0.6:
                x1, y1, x2, y2 = map(int, box)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width - 1, x2), min(height - 1, y2)

                if x2 <= x1 or y2 <= y1:
                    continue

                roi = image[y1:y2, x1:x2]

                if roi.size > 0:
                    blurred_roi = cv2.GaussianBlur(roi, (51, 51), 0)
                    image[y1:y2, x1:x2] = blurred_roi

        return image, has_class_5_below_with_high_conf
    
    def calculate_depth_at_center(self, depth_image, center_x, center_y, box_width, box_height):
        height, width = depth_image.shape

        # 박스 좌표 계산
        top_left_x = max(center_x - box_width // 2, 0)
        top_left_y = max(center_y - box_height // 2, 0)
        bottom_right_x = min(center_x + box_width // 2, width)
        bottom_right_y = min(center_y + box_height // 2, height)

        # 박스 내 깊이값 추출
        box_depth_values = depth_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x].flatten()

        # 유효한 깊이값 필터링 (0 < depth <= 15미터)
        valid_depths = 312.15 * 7.5 / box_depth_values[box_depth_values > 0]
        valid_depths = valid_depths[valid_depths <= 15.0]

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
        boxes_xyxys = result.boxes.xyxy.cpu().numpy()  

        height, width = depth_img.shape
        results = []
        
        for box, class_id, confidence, boxes_xyxy in zip(boxes, class_ids, confidences, boxes_xyxys):
            # 박스 좌표 (정규화된 값 → 픽셀 단위)
            center_x, center_y = int(box[0] * width), int(box[1] * height)
            box_width, box_height = int(box[2] * width), int(box[3] * height)
            x1, y1, x2, y2 = boxes_xyxy
            
            # 깊이값 추출
            mean_depth_m = self.calculate_depth_at_center(depth_img, center_x, center_y, box_width, box_height)
            if mean_depth_m:
                results.append((class_id, mean_depth_m, confidence, center_x, center_y, box_width, box_height, x1, y1, x2, y2))
            
        return results if results else None  # 리스트가 비어 있으면 None 반환
    
    def save_rawimage(self, cv_image, save_path):
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
