#!/usr/bin/python3
# coding=utf8

"""
猜拳游戏 机器人控制模块 V2.0
"""

import os
import sys
import time
import traceback

# 添加utils的asr_vosk.py路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.asr_vosk import AsrVosk
# 替换hiwonder.TTS为大模型接口
from large_models_interfaces.Text2Speech_interface import CosyVoiceModel
import hiwonder.ros_robot_controller_sdk as rrc
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
from ActionGroupDict import *

class RobotController:

    # 定义语音命令ID常量
    CMD_PLAY_GAME = (1, 2)  # 开始游戏命令ID
    CMD_EXIT_GAME = (3, 4)  # 退出游戏命令ID

    # 参考asr_vosk.py中的hotwords_dict定义语音命令字典
    hotwords_dict = {"猜拳": 1, "再来": 2, "再见":3, "不玩了":4}

    def __init__(self):
        """初始化机器人控制器"""
        # 加载舵机参数
        self.servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)
        # 初始化板卡控制器
        self.board = rrc.Board()
        self.asr = None  # 延迟初始化ASR
        self.tts = None  # 延迟初始化TTS
        self._initialize_hardware()

    def _initialize_hardware(self):
        """初始化硬件组件"""
        try:
            # 初始化TTS，使用大模型接口
            self.tts = CosyVoiceModel()

            # 舵机初始化 - 使用新的API
            self.board.pwm_servo_set_position(0.5, [[1, 1500]])  # 时间单位为秒，会在内部转换为毫秒
            self.board.pwm_servo_set_position(0.5, [[2, self.servo_data['servo2']]])
            AGC.runActionGroup('stand')

            self.is_hardware_ready = True

        except Exception as e:
            print("初始化：硬件初始化失败:", e)
            print(traceback.format_exc())
            self.is_hardware_ready = False

    def _initialize_asr(self):
        """延迟初始化ASR，只在需要时初始化"""
        if self.asr is None:
            try:
                # 请确保模型路径正确
                model_path = "../models/vosk-model-small-cn-0.22"  # 根据实际路径调整
                if not os.path.exists(model_path):
                    print(f"错误：Vosk模型未找到！请下载模型并放置在 {model_path}")
                    print("下载地址：https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip")
                    return False
                
                self.asr = AsrVosk(model_path, self.hotwords_dict)
                return True
            except Exception as e:
                print(f"ASR初始化失败: {e}")
                return False
        return True

    def speak(self, text):
        """TTS播报文本
        
        Args:
            text: 要播报的文本
        """
        try:
            if self.tts is not None:
                # 修改为使用大模型接口的text2speech方法
                self.tts.text2speech(text)
                # 给TTS足够的播放时间
                sleep_time = min(max(len(text) * 0.15, 0.8), 3)
                time.sleep(sleep_time)
            else:
                print("TTS：TTS未初始化")
        except Exception as e:
            print(f"TTS：TTS播放失败: {e}")
            print(f"TTS：语音播报失败，文本内容: {text}")

    def perform_gesture(self, gesture_name):
        """执行手势动作
        
        Args:
            gesture_name: 手势名称，如"石头"、"剪刀"、"布"
        """
        action_map = {
            "剪刀": "jiandao",
            "石头": "shitou",
            "布": "bu"
        }
        
        if gesture_name in action_map:
            AGC.runActionGroup(action_map[gesture_name])
    
    def perform_emotion(self, emotion_name):
        """执行情绪动作
        
        Args:
            emotion_name: 情绪名称，如"胜利"、"失败"
        """
        action_map = {
            "胜利": "twist",  # 胜利动作
            "失败": "cry",     # 失败动作
            "平局": "stand",      # 平局动作
            "关闭": "stand"      # 关闭动作
        }
        
        if emotion_name in action_map:
            AGC.runActionGroup(action_map[emotion_name])

    def get_voice_command(self):
        """获取语音命令
        
        Returns:
            int: 识别到的命令编号，无命令则返回0
        """
        try:
            # 确保ASR已初始化
            if not self._initialize_asr():
                print("语音命令：ASR初始化失败")
                return 0
            
            if self.asr is None:
                print("语音命令：ASR未初始化")
                return 0
                
            result = self.asr.listen_for_hotword()
            # 处理可能的None返回值
            if result is None:
                return 0
            return result
        except Exception as e:
            print(f"语音命令：处理语音命令失败: {e}")
            return 0

    def cleanup(self):
        """清理资源"""
        try:
            if self.asr is not None:
                # 修改为使用AsrVosk的stop方法
                self.asr.stop()
                self.asr = None
        except Exception as e:
            print(f"清理资源时发生错误: {e}")

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.cleanup() 
