#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音控制动作 主程序 V2.0
"""

import os
import sys
import time
import traceback
import threading
from typing import Optional

# 屏蔽ALSA错误消息
os.environ['ALSA_CARD'] = 'none'
os.environ['PYTHONUNBUFFERED'] = '1'

# 重定向stderr到/dev/null以屏蔽ALSA错误
import io
import contextlib

# 获取当前脚本所在文件夹的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上级目录路径
parent_dir = os.path.dirname(current_dir)
# 添加上级目录到系统路径中
sys.path.append(parent_dir)

# 拼接模块路径：~/wxzd/large_models_interfaces
module_path = os.path.join(parent_dir, 'large_models_interfaces')

# 添加到Python路径
if module_path not in sys.path:
    sys.path.append(module_path)

# 添加父目录到系统路径，以便导入utils模块
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# 导入各个模块
from speech_recognizer import SpeechRecognizer
from llm_processor import LLMProcessor
from action_executor import ActionExecutor
from voice_assistant import VoiceAssistant
try:
    from utils.audio import play_wav
except ImportError:
    print("警告：无法导入 utils.audio 模块")
    play_wav = None


class ActionSequenceController:
    """动作序列控制器，整合所有功能模块"""
    
    def __init__(self, play_wav=True):
        """初始化控制器"""
        print("初始化动作序列控制器...")
        
        # 初始化语音助手
        self.voice_assistant = VoiceAssistant()
        
        # 初始化语音识别器
        self.speech_recognizer = SpeechRecognizer()
        
        # 初始化LLM处理器
        self.llm_processor = LLMProcessor()
        
        # 初始化动作执行器
        self.action_executor = ActionExecutor(self.voice_assistant)
        
        print("动作序列控制器初始化完成")
        if play_wav:
            # 播放初始化完成提示音
            try:
                # 检查音频文件是否存在
                audio_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "你好.wav")
                if os.path.exists(audio_file):
                    self.voice_assistant.play_local_audio("你好.wav")
                else:
                    print(f"警告：音频文件不存在: {audio_file}")
            except Exception as e:
                print(f"播放音频文件时出错: {e}")
    
    def run_once(self, request_text="") -> bool:
        """
        执行一次完整的语音控制流程
        
        Returns:
            bool: 是否成功执行
        """
        try:
            if request_text == "":
                # 1. 通过语音识别获取用户指令
                command_text = self.speech_recognizer.listen()
                if not command_text:
                    return False
            else:
                command_text = request_text
            # 2. 在另一个线程中播放"好的.wav"
            try:
                # 检查音频文件是否存在
                audio_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "好的.wav")
                if os.path.exists(audio_file):
                    threading.Thread(
                        target=self.voice_assistant.play_local_audio,
                        args=("好的.wav", False),
                        daemon=True
                    ).start()
                else:
                    print(f"警告：音频文件不存在: {audio_file}")
            except Exception as e:
                print(f"播放音频文件时出错: {e}")
            
            # 3. 通过LLM处理器将自然语言指令转换为动作序列
            result = self.llm_processor.process_command(command_text)
            
            # 4. 播报处理结果并等待播放完成
            text_response = result.get("text_response", "")
            if text_response:
                self.voice_assistant.speak(text_response)
            
            # 5. 执行动作序列
            action_sequence = result.get("action_sequence", [])
            if not action_sequence:
                return False
            
            self.action_executor.execute_sequence(action_sequence)
            return True
            
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            return False
        except Exception as e:
            print(f"执行过程中出错: {e}")
            print(traceback.format_exc())
            return False
    
    def run_loop(self) -> None:
        """持续监听并执行用户指令"""
        print("=" * 50)
        print("动作序列控制器已启动，可以开始语音控制")
        print("按 Ctrl+C 退出程序")
        print("=" * 50)
        
        try:
            while True:
                self.run_once()
                time.sleep(1)  # 短暂暂停后继续监听
        except KeyboardInterrupt:
            print("\n程序被用户中断，即将退出")


def main():
    """主函数"""
    try:
        # 屏蔽ALSA错误
        stderr_fd = os.dup(2)  # 保存原始stderr
        devnull = open(os.devnull, 'w')
        os.dup2(devnull.fileno(), 2)  # 将stderr重定向到/dev/null
        
        controller = ActionSequenceController()
        controller.run_loop()
        
        # 恢复stderr
        os.dup2(stderr_fd, 2)
        devnull.close()
        
    except Exception as e:
        print(f"程序运行出错: {e}")
        print(traceback.format_exc())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main()) 