#!/usr/bin/python3
# coding=utf8

"""
猜拳游戏 相机操作和图像捕获模块 V2.0
"""

import os
import cv2
import sys
from pathlib import Path

# 添加TonyPi路径
sys.path.append('/home/pi/TonyPi/')
import hiwonder.Camera as Camera

class ImageCapture:
    """图像捕获：负责相机操作和图像捕获"""
    
    def __init__(self):
        """初始化相机"""
        self.camera = Camera.Camera()
        self.camera.camera_open()
        self.default_save_dir = Path('/home/pi/wxzd/rps/img')
        
        # 确保保存目录存在
        self.default_save_dir.mkdir(exist_ok=True)
    
    def capture_image(self, save_path=None):
        """捕获图像并保存
        
        Args:
            save_path: 保存路径
            
        Returns:
            str: 保存的图像路径，失败则返回None
        """
        if save_path is None:
            save_path = str(self.default_save_dir / 'rps.jpg')
            
        ret, frame = self.camera.read()
        if not ret:
            print("图像捕获：拍照失败")
            return None
            
        cv2.imwrite(save_path, frame)
        # print(f"图像捕获：图像已保存至 {save_path}")
        return save_path
    
    def close(self):
        """关闭相机"""
        self.camera.camera_close()
        print("程序关闭：摄像头已关闭") 