"""
图像描述接口 测试脚本 V2.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. 导入接口
from large_models_interfaces.image_describe_interface import QwenVLModelInterface

# 2. 初始化接口
vision_model = QwenVLModelInterface(model="qwen-vl-max")

# 3. 指定图片路径以及提问
img_path = './test.jpg'
question = '描述一下图片，并且数出图片中有几个人'

# 4. 提问
description = vision_model.describe_image(image_path=img_path, prompt=question)

print(description)
