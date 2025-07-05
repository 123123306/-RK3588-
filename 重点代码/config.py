import os

# 摄像头配置
CAMERA_RESOLUTION = (1920, 1080)
SUB_IMAGE_SIZE = (640, 640)
SUB_IMAGE_REGIONS = [
    (0, 0, 640, 640),          # 左上区域
    (640, 0, 640, 640),       # 中间区域
    (1280, 0, 640, 640)       # 右上区域
]

# 路径配置
BASE_FOLDER = "/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo"
CAPTURED_IMAGE_PATH = os.path.join(BASE_FOLDER, "camera_image_19201080/captured_image.jpg")
SUB_IMAGE_OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "rknn_input_image_640640")
OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "rknn_output_image_640640")
MODEL_PATH = os.path.join(BASE_FOLDER, "model/best.rknn")
DEMO_EXECUTABLE = os.path.join(BASE_FOLDER, "rknn_yolov8_demo")

# 调试标志 (全部设置为False以去除调试代码)
DEBUG_CAMERA = False
DEBUG_IMAGE_PROCESSOR = False
