#!/usr/bin/python3
# coding=utf8

"""
场景识别 主程序 V2.0
"""

import os
import sys
import traceback

# 添加项目根目录到系统路径，确保可以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要的模块
from voice_recognition import VoiceRecognition

def main():
    """程序主入口，直接执行场景识别"""
    # 检查API密钥
    if not os.environ.get('ALI_APIKEY'):
        print("警告：未设置环境变量ALI_APIKEY，请设置后再运行")
        return "请配置ALI_APIKEY环境变量"
        
    try:
        print("启动视觉大模型识别...")
        
        # 创建语音识别器实例
        voice_recognizer = VoiceRecognition()
        
        try:
            print("正在执行场景识别...")
            # 直接调用recognize_image方法
            voice_recognizer.recognize_image()
            print("场景识别已完成")
            return "场景识别已完成，结果已通过语音播报"
        finally:
            # 确保资源被释放
            if hasattr(voice_recognizer, 'cleanup') and callable(voice_recognizer.cleanup):
                voice_recognizer.cleanup()
                
    except Exception as e:
        error_message = f"场景识别失败: {e}"
        print(error_message)
        traceback.print_exc()
        return f"场景识别出错: {str(e)}"

if __name__ == '__main__':
    try:
        result = main()
        print(result)
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    except Exception as e:
        print(f"\n程序发生错误: {e}")
        traceback.print_exc()
