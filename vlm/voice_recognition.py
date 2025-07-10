#!/usr/bin/python3
# coding=utf8

"""
场景识别 语音识别系统模块 V2.0
"""

import os
import sys
import time
import threading
import traceback
import subprocess

# 添加项目根目录到系统路径，确保可以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入utils中的asr_vosk模块
from utils.asr_vosk import AsrVosk

# 导入自定义的视觉大模型识别器
from image_recognition import ImageRecognition

class VoiceRecognition:
    """语音识别系统：通过语音激活，拍照并识别图像内容"""
    
    def __init__(self):        
        # 创建音频文件路径
        self.audio_path = os.path.join('/home/pi/wxzd/vlm')
        os.makedirs(self.audio_path, exist_ok=True)
        
        # 系统状态
        self.is_running = False
        self.is_processing = False
            
        # 初始化图像识别器
        self.image_recognizer = ImageRecognition()
        
    def play_audio(self, audio_file):
        """播放音频文件，不显示输出"""
        if not os.path.exists(audio_file):
            print(f"音频文件不存在: {audio_file}")
            return
            
        try:
            # 使用subprocess并将输出重定向到/dev/null以避免显示播放信息
            subprocess.run(["aplay", "-q", audio_file], 
                          stdout=subprocess.DEVNULL, 
                          stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"播放音频失败: {e}")
            
    def play_audio_thread(self, audio_file):
        """在单独线程中播放音频文件"""
        thread = threading.Thread(target=self.play_audio, args=(audio_file,))
        thread.daemon = True
        thread.start()
        return thread
            
    def recognize_image(self):
        """拍照并识别图像内容"""
        self.is_processing = True
        audio_thread = None
        
        try:
            # 播放提示音 - 在单独线程中播放，同时进行拍照
            let_me_see_file = os.path.join(self.audio_path, "让我看看.wav")
            if os.path.exists(let_me_see_file):
                print("开始播放语音并拍照...")
                audio_thread = self.play_audio_thread(let_me_see_file)
            else:
                print("找不到语音文件")
            
            # 同时进行拍照操作
            image_path = self.image_recognizer.capture_image()
            
            # 等待音频播放完成，最多等待2秒
            if audio_thread and audio_thread.is_alive():
                print("等待语音播放完成...")
                audio_thread.join(timeout=2.0)
                
            # 检查拍照结果
            if not image_path:
                print("拍照失败")
                return
                
            # 识别图像
            print("开始分析图像...")
            description = self.image_recognizer.analyze_image(image_path)
            if not description:
                print("无法识别图像")
                return
                
            # 朗读识别结果
            self.image_recognizer.speak_description(description)
            
        except Exception as e:
            print(f"识别过程出错: {e}")
            print(traceback.format_exc())
        finally:
            self.is_processing = False
            self.cleanup()
            
            
    def cleanup(self):
        """清理资源"""
        self.is_running = False
        self.image_recognizer.close()

        print("资源已清理") 