#!/usr/bin/python3
# coding=utf8

"""
猜拳游戏 游戏规则和胜负判断 V2.0
"""

import random

class GameJudge:
    """游戏裁判：负责游戏规则和胜负判断"""
    
    def __init__(self):
        """初始化游戏裁判"""
        self.options = ["石头", "剪刀", "布"]
    
    def select_robot_move(self):
        """机器人随机选择出拳
        
        Returns:
            str: 机器人选择的手势
        """
        return random.choice(self.options)
    
    def determine_winner(self, robot_move, human_move):
        """判断胜负
        
        Args:
            robot_move: 机器人的出拳
            human_move: 人类的出拳
            
        Returns:
            str: 结果，包括"机器人胜"、"人类胜"、"平局"或"无效"
        """
        if human_move == "无结果":
            return "无效"
        
        if robot_move == human_move:
            return "平局"
        
        if (robot_move == "石头" and human_move == "剪刀") or \
           (robot_move == "剪刀" and human_move == "布") or \
           (robot_move == "布" and human_move == "石头"):
            return "机器人胜"
        else:
            return "人类胜" 