import cv2
import os
from camera_controller import CameraController
from image_processor import ImageProcessor
from yolov8 import RKNNYOLOv8Detector
from config import (
    CAMERA_RESOLUTION,
    SUB_IMAGE_REGIONS,
    CAPTURED_IMAGE_PATH,
    SUB_IMAGE_OUTPUT_FOLDER,
    MODEL_PATH,
    DEMO_EXECUTABLE,
    OUTPUT_FOLDER
)


def main():
    # 确保输出文件夹存在
    os.makedirs(os.path.dirname(CAPTURED_IMAGE_PATH), exist_ok=True)
    os.makedirs(SUB_IMAGE_OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # 初始化摄像头控制器
    camera = CameraController()

    try:
        # 1. 捕获图像
        image = camera.capture_image()
        print("Image captured successfully.")
        cv2.imwrite(CAPTURED_IMAGE_PATH, image)  # 保存完整图像

        # 2. 分割图像
        processor = ImageProcessor()
        sub_images = processor.split_image(image)

        # 3. 保存并处理分割后的子图像
        sub_image_paths = []
        for i, sub_image in enumerate(sub_images, start=1):
            sub_image_path = os.path.join(SUB_IMAGE_OUTPUT_FOLDER, f"sub_image_{i}.jpg")
            cv2.imwrite(sub_image_path, sub_image)
            print(f"Sub-image {i} saved to {sub_image_path}")
            sub_image_paths.append(sub_image_path)

        # 4. 初始化YOLOv8检测器
        detector = RKNNYOLOv8Detector(
            demo_executable=DEMO_EXECUTABLE,
            model_path=MODEL_PATH,
            input_folder=SUB_IMAGE_OUTPUT_FOLDER,
            output_folder=OUTPUT_FOLDER
        )

        # 5. 对所有子图像运行检测
        detection_results = detector.run_detection_on_folder()

        # 6. 输出检测结果
        for result in detection_results:
            image_name = result['image_file']
            detections = result['results']
            print(f"\nResults for {image_name}:")
            for detection in detections:
                print(f"  Class: {detection['class_name']}, "
                      f"Coordinates: ({detection['x1']}, {detection['y1']}) to ({detection['x2']}, {detection['y2']}), "
                      f"Confidence: {detection['confidence']}")

    finally:
        # 释放摄像头资源
        camera.release()
        os.system('python /home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/pythonProject/motor_controller.py')

if __name__ == "__main__":
    main()
