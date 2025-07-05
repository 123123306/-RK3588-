import sys
import subprocess
import os
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTextEdit,
                             QGridLayout, QGroupBox)
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PIL import Image
import platform

# ========== 配置部分 ==========
# 子图文件夹路径
ORIGINAL_SUB_DIR = "/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/rknn_input_image_640640"
DETECTION_SUB_DIR = "/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/rknn_output_image_640640"

# 子图文件名
ORIGINAL_SUB_NAMES = ["sub_image_1.jpg", "sub_image_2.jpg", "sub_image_3.jpg"]
DETECTION_SUB_NAMES = ["sub_image_1_out.png", "sub_image_2_out.png", "sub_image_3_out.png"]

# 拼接后图像保存路径
ORIGINAL_IMAGE_PATH = "/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/combined_original.jpg"
DETECTION_IMAGE_PATH = "/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/combined_detection.jpg"

# 命令配置
WORKING_DIRECTORY = "/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/pythonProject"
CONDA_ENV_NAME = "py39_tkl2-2.1.0"  # conda环境名
MAIN_PROGRAM = "main.py"  # 主程序名
CONDA_PATH = "/home/elf/lishuhua/APP/miniconda3/bin/conda"  # conda可执行文件路径

# 窗口配置
WINDOW_TITLE = "茶叶分拣"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# 数据更新和图像刷新间隔(秒)
IMAGE_REFRESH_INTERVAL = 5  # 图像刷新间隔
PROCESS_CHECK_INTERVAL = 1  # 检查进程状态的间隔

# 延迟时间(秒)
ORIGINAL_IMAGE_DELAY = 4  # 原图延迟
DETECTION_IMAGE_DELAY = 15  # 检测图延迟
DATA_LOAD_DELAY = 15  # 数据文件延迟

# 数据文件配置
DATA_FILE_PATH = "/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/impurity_data/impurity_results.txt"

# 界面文本
DATA_DISPLAY_TITLES = [
    "杂质总数:", "rolled类型杂质数量:",
    "loose类型杂质数量:", "stem类型杂质数量:"
]


# ========== 程序代码 ==========
class DataUpdateThread(QThread):
    """数据更新线程，用于从txt文件获取数据"""
    data_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = False

    def run(self):
        while self.running:
            try:
                if not os.path.exists(DATA_FILE_PATH):
                    time.sleep(1)
                    continue

                with open(DATA_FILE_PATH, 'r') as f:
                    lines = f.readlines()

                data = {'total': 0, 'rolled': 0, 'loose': 0, 'stem': 0}
                for line in lines:
                    line = line.strip()
                    if line.startswith("Total:"):
                        data['total'] = int(line.split(":")[1].strip())
                    elif line.startswith("rolled:"):
                        data['rolled'] = int(line.split(":")[1].strip())
                    elif line.startswith("loose:"):
                        data['loose'] = int(line.split(":")[1].strip())
                    elif line.startswith("stem:"):
                        data['stem'] = int(line.split(":")[1].strip())

                self.data_updated.emit(data)
                time.sleep(1)
            except Exception as e:
                print(f"读取数据时出错: {str(e)}")
                time.sleep(1)

    def start_loading(self):
        self.running = True
        self.start()

    def stop(self):
        self.running = False
        self.wait()


class LogDisplayWidget(QWidget):
    """日志显示组件"""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.start_btn = QPushButton('启动')
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet('''
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        ''')
        layout.addWidget(self.start_btn)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet('''
            QTextEdit {
                background-color: #f0f0f0;
                font-family: Consolas, monospace;
                font-size: 12px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        ''')
        layout.addWidget(self.log_text)
        self.setLayout(layout)

    def append_log(self, message):
        current_time = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{current_time}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def set_stop_mode(self):
        self.start_btn.setText("停止")
        self.start_btn.setStyleSheet('''
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #d32f2f; }
        ''')

    def set_start_mode(self):
        self.start_btn.setText("启动")
        self.start_btn.setStyleSheet('''
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
        ''')


class DataDisplayWidget(QWidget):
    """数据显示组件"""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        layout.setVerticalSpacing(15)
        font = QFont()
        font.setPointSize(12)
        self.value_labels = []

        for i, label_text in enumerate(DATA_DISPLAY_TITLES):
            label = QLabel(label_text)
            label.setFont(font)
            label.setMinimumHeight(30)
            layout.addWidget(label, i, 0, 1, 1)

            value_label = QLabel("0")
            value_label.setFont(font)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setStyleSheet("font-weight: bold; color: #333;")
            value_label.setMinimumHeight(30)
            layout.addWidget(value_label, i, 1, 1, 1)
            self.value_labels.append(value_label)

        layout.setRowStretch(len(DATA_DISPLAY_TITLES), 1)
        self.setLayout(layout)

    def update_data(self, data):
        values = [
            data.get('total', 0),
            data.get('rolled', 0),
            data.get('loose', 0),
            data.get('stem', 0)
        ]
        for i, value in enumerate(values):
            self.value_labels[i].setText(str(value))


class ImageDisplayWidget(QWidget):
    """图像显示组件"""

    def __init__(self, title, image_path=None):
        super().__init__()
        self.title = title
        self.image_path = image_path
        self.original_pixmap = None
        self.last_size = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        layout.addWidget(self.image_label, 1)
        self.setLayout(layout)
        self.image_label.setText("等待启动后加载图像...")

    def load_image(self, image_path=None):
        if image_path is None:
            image_path = self.image_path
        if not os.path.exists(image_path):
            self.image_label.setText(f"图像不存在: {image_path}")
            self.original_pixmap = None
            return False

        try:
            self.original_pixmap = QPixmap(image_path)
            if not self.original_pixmap.isNull():
                self._resize_image()
                return True
            else:
                self.image_label.setText(f"无法加载图像: {image_path}")
                self.original_pixmap = None
                return False
        except Exception as e:
            self.image_label.setText(f"加载图像时出错: {str(e)}")
            self.original_pixmap = None
            return False

    def _resize_image(self):
        if not self.original_pixmap or self.original_pixmap.isNull():
            return
        target_size = self.image_label.size()
        if self.last_size == target_size:
            return
        self.last_size = target_size

        max_scale = 5.0
        original_size = self.original_pixmap.size()
        scale_factor = min(
            target_size.width() / original_size.width(),
            target_size.height() / original_size.height(),
            max_scale
        )
        scaled_width = int(original_size.width() * scale_factor)
        scaled_height = int(original_size.height() * scale_factor)

        scaled_pixmap = self.original_pixmap.scaled(
            scaled_width, scaled_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        if self.original_pixmap and not self.original_pixmap.isNull():
            QTimer.singleShot(100, self._resize_image)
        super().resizeEvent(event)


def combine_images(sub_dir, sub_names, output_path):
    """拼接三张640x640的子图为一张1920x640的大图"""
    try:
        for sub_name in sub_names:
            sub_path = os.path.join(sub_dir, sub_name)
            if not os.path.exists(sub_path):
                raise FileNotFoundError(f"子图不存在: {sub_path}")

        images = []
        for sub_name in sub_names:
            sub_path = os.path.join(sub_dir, sub_name)
            img = Image.open(sub_path)
            images.append(img)

        combined_image = Image.new('RGB', (640 * 3, 640))
        for i, img in enumerate(images):
            combined_image.paste(img, (i * 640, 0))
        combined_image.save(output_path)
        return True
    except Exception as e:
        print(f"拼接图像时出错: {str(e)}")
        return False


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.process = None
        self.data_thread = None
        self.startup_time = 0
        self.is_running = False
        self.steps_completed = [False, False, False]  # 跟踪步骤完成情况

        # 初始化定时器
        self.process_check_timer = QTimer()
        self.image_timer = QTimer()
        self.delayed_actions_timer = QTimer()

        # 连接信号
        self.process_check_timer.timeout.connect(self.check_process_status)
        self.image_timer.timeout.connect(self.refresh_images)
        self.delayed_actions_timer.timeout.connect(self.check_delayed_actions)

        self.initUI()

    def initUI(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QGridLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)

        # 图像显示区域
        self.original_image_widget = ImageDisplayWidget("摄像头拍摄原图")
        main_layout.addWidget(self.original_image_widget, 0, 0, 1, 1)

        self.detection_image_widget = ImageDisplayWidget("目标检测结果图")
        main_layout.addWidget(self.detection_image_widget, 0, 1, 1, 1)

        # 数据显示区域
        data_group = QGroupBox("茶叶杂质检测结果数据")
        data_layout = QVBoxLayout()
        data_layout.setContentsMargins(10, 15, 10, 10)
        self.data_display_widget = DataDisplayWidget()
        data_layout.addWidget(self.data_display_widget)
        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group, 1, 0, 1, 1)

        # 日志区域
        log_group = QGroupBox("日志信息")
        log_layout = QVBoxLayout()
        self.log_display_widget = LogDisplayWidget()
        log_layout.addWidget(self.log_display_widget)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1, 1, 1, 1)

        # 连接启动按钮
        self.log_display_widget.start_btn.clicked.connect(self.toggle_process)

        # 启动定时器
        self.process_check_timer.start(PROCESS_CHECK_INTERVAL * 1000)

    def toggle_process(self):
        """切换启动/停止状态"""
        if not self.is_running:
            self.start_process()
        else:
            self.stop_process()

    def start_process(self):
        """启动处理流程"""
        if self.process and self.process.poll() is None:
            self.log_display_widget.append_log("程序正在运行中...")
            return

        # 重置状态
        self.steps_completed = [False, False, False]
        self.is_running = True
        self.log_display_widget.set_stop_mode()
        self.log_display_widget.start_btn.setEnabled(True)

        self.log_display_widget.append_log("准备启动程序...")
        self._launch_subprocess()

        # 记录启动时间
        self.startup_time = time.time()

        # 启动延迟动作检查定时器
        if not self.delayed_actions_timer.isActive():
            self.delayed_actions_timer.start(100)  # 每100ms检查一次延迟动作

        # 启动图像刷新定时器
        if not self.image_timer.isActive():
            self.image_timer.start(IMAGE_REFRESH_INTERVAL * 1000)

    def stop_process(self):
        """停止处理流程"""
        self.log_display_widget.append_log("正在停止所有操作...")
        self.is_running = False

        # 停止定时器
        self.delayed_actions_timer.stop()

        # 终止进程
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.process = None

        # 停止数据线程
        if self.data_thread:
            self.data_thread.stop()
            self.data_thread = None

        # 重置界面
        self.original_image_widget.image_label.setText("等待启动后加载图像...")
        self.detection_image_widget.image_label.setText("等待启动后加载图像...")
        self.data_display_widget.update_data({'total': 0, 'rolled': 0, 'loose': 0, 'stem': 0})

        self.log_display_widget.set_start_mode()
        self.log_display_widget.append_log("所有操作已停止")

    def _launch_subprocess(self):
        """使用 conda run 在后台启动子程序"""
        try:
            conda_run_cmd = [
                CONDA_PATH,
                "run",
                "--no-capture-output",
                "-n",
                CONDA_ENV_NAME,
                "python",
                os.path.join(WORKING_DIRECTORY, MAIN_PROGRAM)
            ]

            log_path = os.path.join(WORKING_DIRECTORY, "subprocess.log")
            with open(log_path, "a") as log_file:
                self.process = subprocess.Popen(
                    conda_run_cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=WORKING_DIRECTORY,
                    preexec_fn=os.setsid
                )
            self.log_display_widget.append_log(f"子程序已启动（PID: {self.process.pid}）")
        except Exception as e:
            self.log_display_widget.append_log(f"启动失败: {str(e)}")
            self.stop_process()

    def check_delayed_actions(self):
        """检查并执行延迟动作"""
        if not self.is_running:
            return

        if not self.process or self.process.poll() is not None:
            self.stop_process()
            return

        current_time = time.time()
        elapsed = current_time - self.startup_time

        # 4秒后加载原图（步骤1）
        if elapsed >= ORIGINAL_IMAGE_DELAY and not self.steps_completed[0]:
            self.load_original_image()
            self.steps_completed[0] = True

        # 10秒后加载检测图（步骤2）
        if elapsed >= DETECTION_IMAGE_DELAY and not self.steps_completed[1]:
            self.load_detection_image()
            self.steps_completed[1] = True

        # 15秒后加载数据（步骤3）
        if elapsed >= DATA_LOAD_DELAY and not self.steps_completed[2]:
            self.load_data_file()
            self.steps_completed[2] = True

            # 数据加载完成后启动持续更新线程
            if not self.data_thread:
                self.data_thread = DataUpdateThread()
                self.data_thread.data_updated.connect(self.update_data)
                self.data_thread.start_loading()

    def load_original_image(self):
        """加载原始图像"""
        self.log_display_widget.append_log("开始拼接并加载原始图像...")
        if combine_images(ORIGINAL_SUB_DIR, ORIGINAL_SUB_NAMES, ORIGINAL_IMAGE_PATH):
            self.log_display_widget.append_log("原始图像拼接成功")
            if self.original_image_widget.load_image(ORIGINAL_IMAGE_PATH):
                self.log_display_widget.append_log("原始图像加载成功")
            else:
                self.log_display_widget.append_log("原始图像加载失败")
        else:
            self.log_display_widget.append_log("原始图像拼接失败")

    def load_detection_image(self):
        """加载检测图像"""
        self.log_display_widget.append_log("开始拼接并加载检测图像...")
        if combine_images(DETECTION_SUB_DIR, DETECTION_SUB_NAMES, DETECTION_IMAGE_PATH):
            self.log_display_widget.append_log("检测图像拼接成功")
            if self.detection_image_widget.load_image(DETECTION_IMAGE_PATH):
                self.log_display_widget.append_log("检测图像加载成功")
            else:
                self.log_display_widget.append_log("检测图像加载失败")
        else:
            self.log_display_widget.append_log("检测图像拼接失败")

    def load_data_file(self):
        """加载数据文件"""
        self.log_display_widget.append_log("开始读取数据文件...")
        try:
            if not os.path.exists(DATA_FILE_PATH):
                self.log_display_widget.append_log(f"数据文件不存在: {DATA_FILE_PATH}")
                return

            with open(DATA_FILE_PATH, 'r') as f:
                lines = f.readlines()

            data = {'total': 0, 'rolled': 0, 'loose': 0, 'stem': 0}
            for line in lines:
                line = line.strip()
                if line.startswith("Total:"):
                    data['total'] = int(line.split(":")[1].strip())
                elif line.startswith("rolled:"):
                    data['rolled'] = int(line.split(":")[1].strip())
                elif line.startswith("loose:"):
                    data['loose'] = int(line.split(":")[1].strip())
                elif line.startswith("stem:"):
                    data['stem'] = int(line.split(":")[1].strip())

            self.data_display_widget.update_data(data)
            self.log_display_widget.append_log("数据文件加载成功")

        except Exception as e:
            self.log_display_widget.append_log(f"读取数据时出错: {str(e)}")

    def update_data(self, data):
        """更新数据显示"""
        if self.is_running or any(self.steps_completed):  # 只在运行中或已完成步骤时更新
            self.data_display_widget.update_data(data)

    def refresh_images(self):
        """定期刷新图像"""
        if self.steps_completed[0]:  # 如果已经完成了原图加载
            if not self.original_image_widget.image_label.text().startswith("等待"):
                if combine_images(ORIGINAL_SUB_DIR, ORIGINAL_SUB_NAMES, ORIGINAL_IMAGE_PATH):
                    self.original_image_widget.load_image(ORIGINAL_IMAGE_PATH)

        if self.steps_completed[1]:  # 如果已经完成了检测图加载
            if not self.detection_image_widget.image_label.text().startswith("等待"):
                if combine_images(DETECTION_SUB_DIR, DETECTION_SUB_NAMES, DETECTION_IMAGE_PATH):
                    self.detection_image_widget.load_image(DETECTION_IMAGE_PATH)

    def check_process_status(self):
        """检查子程序状态"""
        if self.process and self.process.poll() is not None:
            return_code = self.process.poll()
            if return_code == 0:
                self.log_display_widget.append_log("子程序已正常退出")
            else:
                self.log_display_widget.append_log(f"子程序异常退出（代码: {return_code}）")

            if self.is_running:
                self.stop_process()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_running:
            self.stop_process()

        if self.data_thread:
            self.data_thread.stop()

        self.image_timer.stop()
        self.process_check_timer.stop()
        self.delayed_actions_timer.stop()

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    font = QFont("SimHei")
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
