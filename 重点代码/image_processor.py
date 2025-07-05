import cv2
import numpy as np
import os
from config import SUB_IMAGE_SIZE, SUB_IMAGE_REGIONS, SUB_IMAGE_OUTPUT_FOLDER


class ImageProcessor:
    @staticmethod
    def split_image(image):
        """将1920x1080图像分割为3张640x640的无重叠图像"""
        sub_images = []
        for i, region in enumerate(SUB_IMAGE_REGIONS):
            x, y, w, h = region
            sub_image = image[y:y + h, x:x + w]
            # 如果图像尺寸不足640x640，填充黑色
            if sub_image.shape[0] < SUB_IMAGE_SIZE[1] or sub_image.shape[1] < SUB_IMAGE_SIZE[0]:
                padded_image = np.zeros((SUB_IMAGE_SIZE[1], SUB_IMAGE_SIZE[0], 3), dtype=np.uint8)
                padded_image[:sub_image.shape[0], :sub_image.shape[1]] = sub_image
                sub_images.append(padded_image)
            else:
                sub_images.append(sub_image)

        return sub_images