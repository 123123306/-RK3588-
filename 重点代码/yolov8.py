import os
import subprocess
import shutil
import re

class RKNNYOLOv8Detector:
    def __init__(self, demo_executable, model_path, input_folder, output_folder):
        """
        初始化 RKNN YOLOv8 检测器
        """
        self.demo_executable = demo_executable
        self.model_path = model_path
        self.input_folder = input_folder
        self.output_folder = output_folder

        # 确保输出文件夹存在
        os.makedirs(self.output_folder, exist_ok=True)

        # 定义正则表达式模式来匹配目标检测结果
        self.pattern = re.compile(r'(\w+)\s@\s\(([\d\s]+)\)\s([\d.]+)')

    def run_detection_on_folder(self):
        """
        对指定文件夹中的所有图片运行 RKNN YOLOv8 检测
        """
        # 获取所有图片文件
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        image_files = [f for f in os.listdir(self.input_folder) if f.lower().endswith(image_extensions)]

        if not image_files:
            return []

        # 用于存储所有检测结果
        all_results = []

        # 对每张图片运行检测
        for image_file in image_files:
            input_path = os.path.join(self.input_folder, image_file)
            output_img_path = os.path.join(self.output_folder, f"{os.path.splitext(image_file)[0]}_out.png")
            output_txt_path = os.path.join(self.output_folder, f"{os.path.splitext(image_file)[0]}_results.txt")

            try:
                # 激活 Conda 环境并运行检测
                cmd = [
                    "conda", "run", "-n", "py39_tkl2-2.1.0",
                    self.demo_executable,
                    self.model_path,
                    input_path
                ]

                # 执行命令并捕获输出
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(self.demo_executable)  # 确保在可执行文件所在目录执行
                )

                if result.returncode != 0:
                    continue

                # 解析目标检测结果
                output_lines = result.stdout.strip().split('\n')
                results_for_image = []

                for line in output_lines:
                    match = self.pattern.match(line)
                    if match:
                        class_name = match.group(1)
                        coordinates = match.group(2).split()  # 提取坐标
                        confidence = match.group(3)

                        if len(coordinates) == 4:
                            x1, y1, x2, y2 = coordinates
                            results_for_image.append({
                                'class_name': class_name,
                                'x1': x1,
                                'y1': y1,
                                'x2': x2,
                                'y2': y2,
                                'confidence': confidence
                            })

                # 保存到 all_results 中
                all_results.append({
                    'image_file': image_file,
                    'results': results_for_image
                })

                # 将生成的图片剪切到输出文件夹并重命名
                source_img_path = os.path.join(os.path.dirname(self.demo_executable), "out.png")
                if os.path.exists(source_img_path):
                    shutil.move(source_img_path, output_img_path)

                # 将检测结果保存到 txt 文件（修改后的部分）
                self.save_results_to_txt(output_txt_path, results_for_image)

            except Exception as e:
                print(f"Error processing {image_file}: {e}")
                continue

        # 返回所有结果，以便其他模块调用
        return all_results

    def save_results_to_txt(self, output_txt_path, results):
        """
        将检测结果保存到 txt 文件，格式为：
        rolled @ (1173 225 1272 423) 0.809
        loose @ (1329 0 1833 330) 0.795
        ...
        """
        with open(output_txt_path, 'w') as f:
            for result in results:
                line = f"{result['class_name']} @ ({result['x1']} {result['y1']} {result['x2']} {result['y2']}) {result['confidence']}\n"
                f.write(line)