#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音控制动作 动作执行器模块 V2.0
"""

import os
import sys
import time
from typing import List, Dict, Optional

# 屏蔽ALSA错误消息
os.environ['ALSA_CARD'] = 'none'

# 导入动作组控制模块
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'TonyPi'))
try:
    import hiwonder.ActionGroupControl as AGC
    from ActionGroupDict import action_group_dict
except ImportError:
    print("警告：无法导入动作控制模块，将使用模拟模式")
    AGC = None


class ActionExecutor:
    """动作执行器，用于执行动作序列"""
    
    def __init__(self, voice_assistant=None):
        """
        初始化动作执行器
        
        Args:
            voice_assistant: 语音助手对象，用于播报动作执行情况
        """
        self.voice_assistant = voice_assistant
        
        # 检查动作控制模块是否可用
        self.action_control_available = AGC is not None
        if not self.action_control_available:
            print("动作控制模块不可用，将使用模拟模式")
        else:
            print("动作执行器初始化成功")
    
    def execute_sequence(self, action_sequence: List[Dict]) -> None:
        """
        执行动作序列
        
        Args:
            action_sequence: 动作序列，包含sequence_id和action_id的字典列表
        """
        if not action_sequence:
            print("动作序列为空，无法执行")
            return
        
        # 确保机器人处于站立状态
        # print("初始化机器人姿态...")
        # self._run_action("stand", True)
        # time.sleep(1)
        
        # 按顺序执行每个动作
        sorted_sequence = sorted(action_sequence, key=lambda x: x['sequence_id'])
        
        print("\n开始执行动作序列")
        print("=" * 30)
        
        for action in sorted_sequence:
            action_id = action.get('action_id')
            sequence_id = action.get('sequence_id')
            
            if not action_id:
                print(f"警告：动作项缺少action_id字段")
                continue
                
            try:
                # 获取动作名称
                action_name = action_group_dict.get(action_id)
                if not action_name:
                    print(f"警告：未找到ID为 {action_id} 的动作")
                    continue
                
                print(f"执行动作 {sequence_id}: {action_name} (ID: {action_id})")
                
                # 执行动作
                self._run_action(action_name)
                time.sleep(0.5)  # 动作间短暂停顿
                
            except Exception as e:
                print(f"执行动作时出错: {e}")
        
        print("=" * 30)
        print("动作序列执行完毕")
        
        # 执行完毕，回到站立姿态
        self._run_action("stand")
    
    def _run_action(self, action_name: str, wait_complete: bool = True) -> None:
        """
        执行单个动作
        
        Args:
            action_name: 动作名称
            wait_complete: 是否等待动作完成
        """
        if self.action_control_available:
            # 实际执行动作
            try:
                AGC.runActionGroup(action_name, 1, wait_complete)
            except Exception as e:
                print(f"执行动作 {action_name} 时出错: {e}")
        else:
            # 模拟动作执行
            print(f"[模拟] 执行动作: {action_name}")
            # 模拟执行时间
            time.sleep(1)


# 测试代码
if __name__ == "__main__":
    # 创建测试动作序列
    test_sequence = [
        {"sequence_id": 1, "action_id": "24"},  # 原地踏步
        {"sequence_id": 2, "action_id": "16"},  # 左勾拳
        {"sequence_id": 3, "action_id": "10"}   # 鞠躬
    ]
    
    # 导入语音助手
    from voice_assistant import VoiceAssistant
    voice_assistant = VoiceAssistant()
    
    # 创建动作执行器并执行测试序列
    executor = ActionExecutor(voice_assistant)
    executor.execute_sequence(test_sequence) 