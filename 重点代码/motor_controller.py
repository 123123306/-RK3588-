from pickle import NONE
import re
import time
import os
CONVERSION_FACTOR = 0.223
DELAY_TIME = 0.0003
from periphery import GPIO

GPIO_CHIP = "/dev/gpiochip3"
LINE_OFFSET_A0 = 0
LINE_OFFSET_A1 = 1
LINE_OFFSET_A2 = 2
LINE_OFFSET_A3 = 3
LINE_OFFSET_A4 = 4
LINE_OFFSET_A5 = 5
LINE_OFFSET_A6 = 6
LINE_OFFSET_B3 = 11
LINE_OFFSET_B4 = 12
LINE_OFFSET_B5 = 13

gpio3_b3 = GPIO(GPIO_CHIP, LINE_OFFSET_B3, "out")
gpio3_b4 = GPIO(GPIO_CHIP, LINE_OFFSET_B4, "out")
gpio3_b5 = GPIO(GPIO_CHIP, LINE_OFFSET_B5, "out")
gpio3_a0 = GPIO(GPIO_CHIP, LINE_OFFSET_A0, "out")
gpio3_a1 = GPIO(GPIO_CHIP, LINE_OFFSET_A1, "out")
gpio3_a2 = GPIO(GPIO_CHIP, LINE_OFFSET_A2, "out")
gpio3_a3 = GPIO(GPIO_CHIP, LINE_OFFSET_A3, "out")
gpio3_a4 = GPIO(GPIO_CHIP, LINE_OFFSET_A4, "out")
gpio3_a5 = GPIO(GPIO_CHIP, LINE_OFFSET_A5, "out")
gpio3_a6 = GPIO(GPIO_CHIP, LINE_OFFSET_A6, "out")

PULSES_PER_REVOLUTION = 400
MM_PER_REVOLUTION = 8

path = '/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/rknn_output_image_640640/'
path1 = '/home/elf/lishuhua/install/rk3588_linux_aarch64/rknn_yolov8_demo/impurity_data/'
num_sub_images = 3
file_paths = [os.path.join(path, f'sub_image_{i}_results.txt') for i in range(1, num_sub_images + 1)]
x_offsets = [0,640,1280]
def calculate_coords(top_left, bottom_right, small_index):
    center_x = (top_left[0] + bottom_right[0]) / 2
    center_y = (top_left[1] + bottom_right[1]) / 2
    ORIGIN_X = 315
    ORIGIN_Y = 702
    if 1 <= small_index <= len(x_offsets):
        big_x = x_offsets[small_index - 1] + center_x
        if big_x < 315 or big_x > 1415:
            return None
        big_y = center_y
        if big_y < 0 or big_y > 640:
            return None
        x_ratio = (big_x - ORIGIN_X) * CONVERSION_FACTOR
        y_ratio = (ORIGIN_Y - big_y) * CONVERSION_FACTOR
        return x_ratio, y_ratio
    else:
        return None, None
def process_impurities(impurities):
    if not impurities:
        return []
    return [res for imp in impurities if (res := calculate_coords(imp["top_left"], imp["bottom_right"], imp["small_index"]))]

impurities = []
impurity_counts = {'rolled': 0, 'loose': 0, 'stem': 0}

for idx, path in enumerate(file_paths, start=1):
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                match = re.search(r'(stem|rolled|loose) @\s*\((\d+)\s+(\d+)\s+(\d+)\s+(\d+)\)', line)
                if match:
                    impurity_type = match.group(1)
                    top_left = (int(match.group(2)), int(match.group(3)))
                    bottom_right = (int(match.group(4)), int(match.group(5)))
                    impurities.append({"top_left": top_left, "bottom_right": bottom_right, "small_index": idx})
                    impurity_counts[impurity_type] += 1
                else:
                    print(f"No match found in {path} for line: {line}")  
    except FileNotFoundError:
        print(f"File {path} not found.")
        
results = process_impurities(impurities)
sorted_results = sorted(results, key=lambda coord: (-coord[0], -coord[1]) if coord is not None else (-float('inf'), -float('inf')))
print("Converted coordinates (sorted from bottom-right to top-left):")
for coord in sorted_results:
        if coord is not None:
            print(coord)

impurities_with_coords = [
    {**imp, 'real_x': x, 'real_y': y} 
    for imp, (x, y) in zip(impurities, results)
]

sorted_impurities = sorted(impurities_with_coords, key=lambda x: (x["real_x"], x["real_y"]), reverse=True)
coords_list = [(imp["real_x"], imp["real_y"]) for imp in sorted_impurities]

output_file = os.path.join(path1, 'impurity_results.txt')
with open(output_file, 'w') as f:
    f.write(f"Total: {len(results)}\n")
    for imp_type, count in impurity_counts.items():
        f.write(f"{imp_type}: {count}\n")
    
print(f"Number of processed impurity coordinates: {len(results)}")
print("Number of each impurity type:")
for imp_type, count in impurity_counts.items():
    print(f"{imp_type}: {count}")

gpio3_b3.write(True)
gpio3_a0.write(True)
gpio3_a3.write(True)

# 在初始化部分添加误差累积变量
error_x = 0.0
error_y = 0.0
error_z = 0.0

try:
    current_x = 0
    current_y = 0
    for index, imp in enumerate(sorted_impurities):
        x = imp['real_x']
        y = imp['real_y']
        distance_z = 10
        
        if index > 0:
            prev_imp = sorted_impurities[index - 1]
            prev_x = prev_imp['real_x']
            prev_y = prev_imp['real_y']
            distance_x = x - prev_x
            distance_y = y - prev_y
        elif index == 0:
            distance_x = x
            distance_y = y
        
        target_pulse_x = (distance_x / MM_PER_REVOLUTION) * PULSES_PER_REVOLUTION + error_x
        target_pulse_y = (distance_y / MM_PER_REVOLUTION) * PULSES_PER_REVOLUTION + error_y
        target_pulse_z = (distance_z / MM_PER_REVOLUTION) * PULSES_PER_REVOLUTION + error_z
        
        pulse_x = int(round(target_pulse_x))
        pulse_y = int(round(target_pulse_y))
        pulse_z = int(round(target_pulse_z))
        
        # 更新误差
        error_x = target_pulse_x - pulse_x
        error_y = target_pulse_y - pulse_y
        error_z = target_pulse_z - pulse_z
        
        print(f'当前 x = {x}, 当前 y = {y}')    

        gpio3_b4.write(False if pulse_x < 0 else True)
        for _ in range(abs(pulse_x)):
            gpio3_b5.write(True)
            time.sleep(DELAY_TIME)
            gpio3_b5.write(False)
            time.sleep(DELAY_TIME)

        gpio3_a1.write(True if pulse_y < 0 else False)
        for _ in range(abs(pulse_y)):
            gpio3_a2.write(True)
            time.sleep(DELAY_TIME)
            gpio3_a2.write(False)
            time.sleep(DELAY_TIME)
        
        gpio3_a4.write(True if pulse_z < 0 else False)
        for _ in range(abs(pulse_z)):
            gpio3_a5.write(True)
            time.sleep(DELAY_TIME)
            gpio3_a5.write(False)
            time.sleep(DELAY_TIME)
        
        gpio3_a6.write(True)
        time.sleep(3) 
        gpio3_a6.write(False)
        time.sleep(0.1)
        
        distance_z = -distance_z
        target_pulse_z = (distance_z / MM_PER_REVOLUTION) * PULSES_PER_REVOLUTION + error_z
        pulse_z = int(round(target_pulse_z))
        error_z = target_pulse_z - pulse_z
        
        gpio3_a4.write(True if pulse_z < 0 else False)
        for _ in range(abs(pulse_z)):
            gpio3_a5.write(True)
            time.sleep(DELAY_TIME)
            gpio3_a5.write(False)
            time.sleep(DELAY_TIME)
            
        current_x = x
        current_y = y

    last_imp = sorted_impurities[-1]
    x=last_imp['real_x']
    y=last_imp['real_y']
    distance_x =x
    distance_y =y
    print(f'laxt_x : {x}, y :last_y {y}') 
    pulse_x = int((distance_x / MM_PER_REVOLUTION) * PULSES_PER_REVOLUTION)
    pulse_y = int((distance_y / MM_PER_REVOLUTION) * PULSES_PER_REVOLUTION)
    gpio3_b4.write(False if pulse_x > 0 else True)
    for _ in range(abs(pulse_x)):
        gpio3_b5.write(True)
        time.sleep(DELAY_TIME)
        gpio3_b5.write(False)
        time.sleep(DELAY_TIME)
    gpio3_a1.write(True if pulse_y > 0 else False)
    for _ in range(abs(pulse_y)):
        gpio3_a2.write(True)
        time.sleep(DELAY_TIME)
        gpio3_a2.write(False)
        time.sleep(DELAY_TIME)  

finally:
    gpio3_b3.write(False)
    gpio3_b3.close()
    gpio3_b4.close()
    gpio3_b5.close()
    gpio3_a0.write(False)
    gpio3_a0.close()
    gpio3_a1.close()
    gpio3_a2.close()
    gpio3_a3.write(False)
    gpio3_a3.close()   
    gpio3_a4.close()
    gpio3_a5.close()
