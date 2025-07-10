#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
场景识别 删除图片工具脚本 V2.0
本脚本独立于场景识别主程序，用来删除"./img"目录下的所有图片文件，直接运行本脚本即可。
"""

import os
import glob

def delete_all_images():
    """删除img目录下的所有图片文件"""
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建img目录的路径
    img_dir = os.path.join(script_dir, 'img')
    
    # 检查img目录是否存在
    if not os.path.exists(img_dir):
        print("错误：img目录不存在")
        return False
    
    # 获取所有图片文件（常见图片格式）
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(img_dir, ext)
        image_files.extend(glob.glob(pattern))
    
    # 检查是否找到图片文件
    if not image_files:
        print("提示：img目录中没有发现图片文件")
        return True
    
    # 计数器
    count = 0
    
    # 删除所有图片文件
    for image_file in image_files:
        try:
            os.remove(image_file)
            count += 1
            print(f"已删除: {os.path.basename(image_file)}")
        except Exception as e:
            print(f"删除 {os.path.basename(image_file)} 时出错: {e}")
    
    print(f"操作完成，共删除 {count} 个图片文件")
    return True

if __name__ == "__main__":
    print("开始删除img目录下的所有图片...")
    delete_all_images()
    print("脚本执行完毕") 