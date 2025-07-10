#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音控制动作 语音识别模块 V2.0
"""

import os
import sys

# 屏蔽ALSA错误消息
os.environ['ALSA_CARD'] = 'none'

# 导入大模型接口模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from large_models_interfaces.Speech2Text_interface import ParaformerModel, ParaformerInterface


class SpeechRecognizer:
    """语音识别类，用于将语音转换为文本"""
    
    def __init__(self):
        """初始化语音识别模型"""
        try:
            # 屏蔽stderr以抑制ALSA错误
            stderr_fd = os.dup(2)  # 保存原始stderr
            devnull = open(os.devnull, 'w')
            os.dup2(devnull.fileno(), 2)  # 将stderr重定向到/dev/null
            
            self.model = ParaformerModel(model="paraformer-realtime-v2", sample_rate=16000)
            
            # 恢复stderr
            os.dup2(stderr_fd, 2)
            devnull.close()
            
            print("语音识别模型初始化成功")
        except Exception as e:
            print(f"语音识别模型初始化失败: {e}")
            sys.exit(1)
            
    def listen(self) -> str:
        """
        监听并识别语音
        
        Returns:
            str: 识别出的文本
        """
        print("正在聆听...")
        try:
            # 屏蔽stderr以抑制ALSA错误
            stderr_fd = os.dup(2)
            devnull = open(os.devnull, 'w')
            os.dup2(devnull.fileno(), 2)
            
            # 调用语音转文本接口
            result = self.model.speech2text()
            
            # 恢复stderr
            os.dup2(stderr_fd, 2)
            devnull.close()
            
            if not result:
                print("未能识别到有效语音输入")
                return ""
            
            print(f"识别结果: {result}")
            return result
        except Exception as e:
            print(f"语音识别出错: {e}")
            return ""


# 测试代码
if __name__ == "__main__":
    # 屏蔽ALSA错误消息
    os.environ['ALSA_CARD'] = 'none'
    
    recognizer = SpeechRecognizer()
    text = recognizer.listen()
    print(f"识别结果: {text}") 