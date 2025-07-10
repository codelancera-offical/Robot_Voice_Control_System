"""
文本转语音接口 测试脚本 V2.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1.导入模块
from large_models_interfaces.Text2Speech_interface import CosyVoiceModel

# 2.初始化模型
CosyVoiceModel = CosyVoiceModel()

text = "你好，欢迎使用语音合成服务。"

# 3.调用接口
CosyVoiceModel.text2speech(text)

