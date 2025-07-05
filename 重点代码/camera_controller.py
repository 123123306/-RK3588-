import cv2
from config import CAMERA_RESOLUTION, CAPTURED_IMAGE_PATH


class CameraController:
    def __init__(self):
        # 初始化摄像头
        self.cap = cv2.VideoCapture(21)
        if not self.cap.isOpened():
            raise Exception("无法打开摄像头")

        # 设置摄像头分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_RESOLUTION[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])

    def capture_image(self):
        """捕获一张图像"""
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("无法从摄像头获取图像")
        return frame

    def release(self):
        """释放摄像头资源"""
        self.cap.release()

    def __del__(self):
        self.release()
