#!/usr/bin/python3
# coding=utf8

"""
猜拳游戏 游戏主要实现 V2.0
"""

import os
import sys
import time
from dashscope import MultiModalConversation

# 导入TonyPi SDK模块
sys.path.append('/home/pi/TonyPi/')
from ActionGroupDict import *

# 导入分离的模块
from image_capture import ImageCapture
from gesture_recognition import GestureRecognition
from robot_controller import RobotController
from game_judge import GameJudge

# 导入音频播放模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.audio import play_wav

class RPSGame:
    """石头剪刀布游戏主类"""
    
    def __init__(self):
        """初始化游戏组件"""
        self.image_capturer = ImageCapture()
        self.gesture_recognizer = GestureRecognition()
        self.robot_controller = RobotController()
        self.game_judge = GameJudge()
        
        # 游戏初始化提示
        if self.robot_controller.is_hardware_ready:
            #print("TTS：猜拳游戏准备就绪")
            #self.robot_controller.speak("猜拳游戏准备就绪")
            #time.sleep(1)
            print("游戏初始化成功")
            print()
        
#         print('''欢迎来和机器人玩猜拳游戏！
# 【语音指令】：
# 猜拳 -> 开始一局猜拳游戏
# 再来 -> 再来一局猜拳游戏
# 再见 -> 退出猜拳游戏
# 不玩了 -> 退出猜拳游戏
# 【键盘控制】：
# 回车键 -> 开始一局猜拳游戏
# ''')
    
    def play_one_round(self):
        """执行一次猜拳游戏"""
        # 播放开始提示
        # self.robot_controller.speak("剪刀石头布")  # 注释掉原TTS播报
        # 播放开始音频文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        play_wav(os.path.join(current_dir, "开始.wav"))
        
        # 机器人选择并执行
        robot_move = self.game_judge.select_robot_move()
        print(f"执行动作：机器人出{robot_move}")
        self.robot_controller.perform_gesture(robot_move)
        
        # 捕获图像
        image_path = self.image_capturer.capture_image()
        if not image_path:
            # self.robot_controller.speak("拍照失败")
            play_wav(os.path.join(current_dir, "拍照失败.wav"))
            return
        
        # 识别人类手势
        human_move = self.gesture_recognizer.recognize_from_image(image_path)
        print(f"手势识别：人类出{human_move}")
        
        # 判断胜负
        result = self.game_judge.determine_winner(robot_move, human_move)
        print(f"游戏结果：{result}")
        print("--------------------------------")
        
        # 根据结果执行相应动作和语音
        self._handle_game_result(result)
    
    def _handle_game_result(self, result):
        """处理游戏结果
        
        Args:
            result: 游戏结果
        """
        # 获取当前文件所在目录路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        if result == "机器人胜":
            # self.robot_controller.speak("哈哈，我赢了")  # 注释掉原TTS播报
            # 播放胜利音频文件
            play_wav(os.path.join(current_dir, "胜利.wav"))
            self.robot_controller.perform_emotion("胜利")
        elif result == "人类胜":
            # self.robot_controller.speak("呜呜呜，我输了")  # 注释掉原TTS播报
            # 播放失败音频文件
            play_wav(os.path.join(current_dir, "失败.wav"))
            self.robot_controller.perform_emotion("失败")
        elif result == "平局":
            # self.robot_controller.speak("居然平了，再来")  # 注释掉原TTS播报
            # 播放平局音频文件
            play_wav(os.path.join(current_dir, "平局.wav"))
            self.robot_controller.perform_emotion("平局")
        else:
            # self.robot_controller.speak("没看清楚，再来")  # 注释掉原TTS播报
            # 播放识别失败音频文件
            play_wav(os.path.join(current_dir, "识别失败.wav"))
            self.robot_controller.perform_emotion("平局")
    
    def run(self):
        """运行游戏主循环"""
        print("猜拳游戏已启动，等待开始...")
        print("--------------------------------")
        try:
            running = True
            while running:
                # 检测语音命令
                command = self.robot_controller.get_voice_command()
                if command in self.robot_controller.CMD_PLAY_GAME:  # 检测到"猜拳"/"再来"指令
                    print("开始猜拳：收到语音命令")
                    self.play_one_round()
                elif command in self.robot_controller.CMD_EXIT_GAME:  # 检测到"再见"/"不玩了"指令
                    print("退出猜拳：收到退出命令")
                    running = False
                
                # 删除键盘输入检测代码
                
                time.sleep(0.01)
        except KeyboardInterrupt:
            print("程序关闭：程序中止")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        self.image_capturer.close()
        # 删除keyboard_monitor清理代码
        self.robot_controller.perform_emotion("关闭")
        print("程序关闭：资源已清理")
