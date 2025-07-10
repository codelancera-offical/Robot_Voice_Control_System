#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音控制动作 语音助手模块 V2.0
"""

import os
import sys
import time
import re
import traceback
import threading

# 屏蔽ALSA错误消息
os.environ['ALSA_CARD'] = 'none'

# 导入大模型语音合成接口
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from large_models_interfaces.Text2Speech_interface import CosyVoiceModel
    from utils.audio import play_wav  # 导入音频播放函数
except ImportError:
    print("警告：无法导入所需模块，将使用文本打印代替语音播报")
    CosyVoiceModel = None
    play_wav = None


class VoiceAssistant:
    """语音助手，用于语音播报和音频反馈"""
    
    def __init__(self):
        """初始化语音助手"""
        # 音频文件目录 - 与Python文件同级目录
        self.audio_dir = os.path.dirname(os.path.abspath(__file__))
        
        try:
            if CosyVoiceModel:
                # 屏蔽ALSA错误消息
                os.environ['ALSA_CARD'] = 'none'  # 抑制ALSA警告
                self.tts = CosyVoiceModel()
                print("语音助手初始化成功")
            else:
                self.tts = None
                print("警告：语音合成模块不可用，将使用文本打印代替语音播报")
        except Exception as e:
            print(f"语音助手初始化失败: {e}")
            self.tts = None
        
        # 用于标记播放是否完成的事件
        self.play_finished = threading.Event()
        self.play_finished.set()  # 初始状态为已完成
    
    def play_local_audio(self, audio_name, blocking=True):
        """
        播放本地音频文件
        
        Args:
            audio_name: 音频文件名，如 "你好.wav"
            blocking: 是否阻塞等待播放完成
        
        Returns:
            bool: 是否成功播放
        """
        # 如果已经在播放，等待完成或返回
        if not self.play_finished.is_set():
            if blocking:
                self.play_finished.wait()
            else:
                return False
        
        # 直接在同级目录查找音频文件
        audio_path = os.path.join(self.audio_dir, audio_name)
        
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            print(f"音频文件不存在: {audio_path}")
            # 即使文件不存在，也设置为完成状态以避免阻塞
            self.play_finished.set()
            return False
        
        # 使用线程播放音频
        self.play_finished.clear()  # 标记为播放中
        
        def play_audio():
            try:
                if play_wav:
                    # 使用utils/audio.py中的play_wav函数播放
                    try:
                        play_wav(audio_path)
                    except Exception as e:
                        print(f"播放音频时出错: {e}")
                        import traceback
                        print(traceback.format_exc())
                else:
                    print(f"无法播放音频，play_wav函数不可用: {audio_name}")
            finally:
                # 标记为播放完成
                self.play_finished.set()
        
        try:
            # 启动播放线程
            play_thread = threading.Thread(target=play_audio)
            play_thread.daemon = True
            play_thread.start()
            
            # 如果是阻塞模式，等待播放完成
            if blocking:
                self.play_finished.wait()
            
            return True
        except Exception as e:
            print(f"创建播放线程时出错: {e}")
            import traceback
            print(traceback.format_exc())
            self.play_finished.set()  # 确保状态一致
            return False
    
    def play_tts_async(self, text):
        """
        异步播放TTS语音
        
        Args:
            text: 要播放的文本
        """
        if not text:
            return
        
        print(f"语音播报: {text}")
        
        # 如果TTS模块不可用，直接返回
        if not self.tts:
            self.play_finished.set()  # 确保状态一致
            return
        
        # 清理文本
        clean_text = self._clean_text_for_tts(text)
        
        # 使用线程播放TTS
        self.play_finished.clear()  # 标记为播放中
        
        def play_tts():
            try:
                try:
                    # 使用通义千问语音合成模型进行播报
                    self.tts.text2speech(clean_text)
                except Exception as e:
                    print(f"语音播报失败: {e}")
                    print(traceback.format_exc())
            finally:
                # 标记为播放完成
                self.play_finished.set()
        
        # 启动播放线程
        play_thread = threading.Thread(target=play_tts)
        play_thread.daemon = True
        play_thread.start()
    
    def wait_for_play_complete(self):
        """等待当前音频播放完成"""
        self.play_finished.wait()
    
    def speak(self, text: str) -> None:
        """
        安全的语音播报函数（同步版本）
        
        Args:
            text: 要播报的文本
        """
        if not text:
            return
        
        # 启动异步播放并等待完成
        self.play_tts_async(text)
        self.wait_for_play_complete()
    
    def _clean_text_for_tts(self, text: str, keep_punctuation: bool = True) -> str:
        """
        清理文本，移除可能导致TTS问题的特殊字符
        
        Args:
            text: 原始文本
            keep_punctuation: 是否保留标点符号
            
        Returns:
            str: 清理后的文本
        """
        if not isinstance(text, str):
            return str(text)
        
        # 移除markdown标记
        text = text.replace('```', '').replace('`', '')
        
        # 保留或移除标点符号
        if not keep_punctuation:
            punctuation = ['，', '。', '！', '？', '；', '：', '"', '"', ''', ''', '、', '《', '》', '（', '）', '【', '】', 
                          '.', ',', '!', '?', ';', ':', '"', "'", '(', ')', '[', ']', '{', '}']
            for p in punctuation:
                text = text.replace(p, '')
        
        # 移除可能导致TTS问题的其他特殊字符
        problematic_chars = ['*', '#', '_', '=', '+', '|', '~', '>', '<']
        for char in problematic_chars:
            text = text.replace(char, '')
        
        return text


# 测试代码
if __name__ == "__main__":
    # 屏蔽ALSA错误消息
    os.environ['ALSA_CARD'] = 'none'
    
    assistant = VoiceAssistant()
    
    # 测试本地音频播放
    print("测试本地音频播放...")
    assistant.play_local_audio("你好.wav")
    
    # 测试TTS
    print("测试TTS播报...")
    assistant.speak("这是一条TTS测试消息") 