#!/usr/bin/python3
# coding=utf8

"""
猜拳游戏 旧版机器人控制 V2.0
"""

import os
import sys
import time
import traceback

# 添加TonyPi路径
sys.path.append('/home/pi/TonyPi/')
import hiwonder.TTS as TTS
import hiwonder.ASR as ASR
import hiwonder.ros_robot_controller_sdk as rrc
import hiwonder.ActionGroupControl as AGC
import hiwonder.yaml_handle as yaml_handle
from ActionGroupDict import *

class RobotController:
    """机器人控制器：负责语音和动作控制"""
    
    # 定义语音命令ID常量
    CMD_PLAY_GAME = 1  # 开始游戏命令ID
    CMD_EXIT_GAME = 2  # 退出游戏命令ID
    
    def __init__(self):
        """初始化机器人控制器"""
        # 加载舵机参数
        self.servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)
        # 初始化板卡控制器
        self.board = rrc.Board()
        self._initialize_hardware()
    
    def _initialize_hardware(self):
        """初始化硬件组件"""
        try:
            # 初始化ASR和TTS
            self.asr = ASR.ASR()
            self.tts = TTS.TTS()
            
            # 清除已有词条
            self.asr.eraseWords()
            self.asr.setMode(1)  # 循环模式
            
            # 添加激活词 - 开始游戏
            self.asr.addWords(self.CMD_PLAY_GAME, 'cai quan')  # 激活词：猜拳
            self.asr.addWords(self.CMD_PLAY_GAME, 'zai lai')   # 激活词：再来
            
            # 添加激活词 - 退出游戏
            self.asr.addWords(self.CMD_EXIT_GAME, 'zai jian')  # 激活词：再见
            self.asr.addWords(self.CMD_EXIT_GAME, 'bu wan le') # 激活词：不玩了
            
            # 舵机初始化 - 使用新的API
            self.board.pwm_servo_set_position(0.5, [[1, 1500]])  # 时间单位为秒，会在内部转换为毫秒
            self.board.pwm_servo_set_position(0.5, [[2, self.servo_data['servo2']]])
            AGC.runActionGroup('stand')
            
            self.is_hardware_ready = True
            
        except Exception as e:
            print("初始化：硬件初始化失败:", e)
            print(traceback.format_exc())
            self.is_hardware_ready = False
    
    def speak(self, text):
        """TTS播报文本
        
        Args:
            text: 要播报的文本
        """
        try:
            self.tts.TTSModuleSpeak('[h0][v10]', text)
            # 给TTS足够的播放时间
            sleep_time = min(max(len(text) * 0.15, 0.8), 3)
            time.sleep(sleep_time)
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
            "失败": "cry"     # 失败动作
        }
        
        if emotion_name in action_map:
            AGC.runActionGroup(action_map[emotion_name])
    
    def get_voice_command(self):
        """获取语音命令
        
        Returns:
            int: 识别到的命令编号，无命令则返回0
        """
        try:
            return self.asr.getResult()
        except Exception as e:
            print(f"语音命令：处理语音命令失败: {e}")
            return 0 