#!/usr/bin/env python3
# encoding:utf-8

"""
场景识别 图像识别处理模块 V2.0
"""

import os
import cv2
import time
import sys

# 添加项目根目录到系统路径，确保可以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入摄像头模块 - 修改为直接从hiwonder导入Camera
import hiwonder.Camera as Camera

# 导入自定义的大模型接口 - 修改导入路径
from large_models_interfaces.image_describe_interface import QwenVLModelInterface
from large_models_interfaces.Text2Speech_interface import CosyVoiceModel

class ImageRecognition:
    """图像识别器：负责拍照、图像分析和语音输出"""
    
    def __init__(self):
        """初始化各个组件"""
        # 初始化摄像头
        self.camera = None
        self.initialize_camera()
        
        # 初始化视觉大模型接口
        self.vlm = QwenVLModelInterface(model="qwen-vl-max")
        
        # 初始化语音合成接口
        self.tts = CosyVoiceModel()
        
        # 创建保存图片的目录
        self.save_dir = "/home/pi/wxzd/vlm/img"
        os.makedirs(self.save_dir, exist_ok=True)
    
    def initialize_camera(self):
        """初始化摄像头"""
        try:
            self.camera = Camera.Camera()
            self.camera.camera_open()
            time.sleep(1)  # 等待摄像头初始化
            print("摄像头初始化成功")
            return True
        except Exception as e:
            print(f"摄像头初始化失败: {e}")
            return False
    
    def capture_image(self):
        """拍摄图片并保存
        
        Returns:
            str: 保存的图像路径，失败返回None
        """
        if self.camera is None:
            if not self.initialize_camera():
                print("无法初始化摄像头")
                return None
        
        # 拍摄图片
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(self.save_dir, f"captured_image_{timestamp}.jpg")
        
        # 读取摄像头图像
        for _ in range(10):  # 多次读取以确保获取到稳定的图像
            ret, frame = self.camera.read()
            if ret and frame is not None:
                break
            time.sleep(0.1)
        
        if not ret or frame is None:
            print("错误：无法获取摄像头图像")
            return None
        
        # 保存图像
        try:
            cv2.imwrite(image_path, frame)
            print(f"图像已保存至: {image_path}")
            return image_path
        except Exception as e:
            print(f"保存图像失败: {e}")
            return None
    
    def analyze_image(self, image_path):
        """使用视觉大模型分析图像
        
        Args:
            image_path (str): 图像文件路径
            
        Returns:
            str: 图像描述结果
        """
        if not image_path or not os.path.exists(image_path):
            print(f"图像文件不存在: {image_path}")
            return None
        
        print("正在分析图像...")
        
        # 优化的提示词，更具体地指导模型生成适合机器人场景的描述
        prompt = """你是一个视觉AI助手，负责根据用户要求返回图片描述，
        注意，你应该生成纯文本来描述，不要以"这张图片展示了xxx"或类似语句开头，可以使用标点符号分割，但不要使用任何特殊符号或者emoji！
        请详细观察并描述图片中的主要物体、人物、动物以及它们的颜色和位置关系。请不要说“图片中没有xxx”这样的句子。
        使用简洁明了的语言，避免复杂句式，便于机器人语音朗读。"""
        
        try:
            # 调用视觉大模型接口
            description = self.vlm.describe_image(image_path, prompt)
            print("--------------------------------")
            print(f"视觉模型描述: {description}")
            print("--------------------------------")
            return description
        except Exception as e:
            print(f"分析图像失败: {e}")
            return None
    
    def speak_description(self, text):
        """使用语音合成接口朗读文本
        
        Args:
            text (str): 要朗读的文本
        """
        if not text:
            text = "无法获取图像描述"
        
        print("正在转换文本为语音...")
        try:
            self.tts.text2speech(text)
            print("语音播放完成")
        except Exception as e:
            print(f"语音合成失败: {e}")
    
    def close(self):
        """关闭资源"""
        if self.camera:
            self.camera.camera_close()
            print("摄像头已关闭")

if __name__ == "__main__":
    # 单独测试图像识别功能
    recognizer = ImageRecognition()
    try:
        image_path = recognizer.capture_image()
        if image_path:
            description = recognizer.analyze_image(image_path)
            if description:
                recognizer.speak_description(description)
    finally:
        recognizer.close() 