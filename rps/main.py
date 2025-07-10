#!/usr/bin/python3
# coding=utf8

"""
猜拳游戏 主程序 V2.0
"""

import os
import sys

# 导入RPS游戏类
from rps_game import RPSGame

def main():
    """程序主入口，执行一局游戏后结束"""
    print("启动石头剪刀布游戏...")
    
    try:
        # 创建游戏实例
        game = RPSGame()
        
        # 执行一局游戏
        game.play_one_round()
        
        print("石头剪刀布游戏已完成")
        return "石头剪刀布游戏已完成"
    except Exception as e:
        print(f"启动石头剪刀布游戏失败: {e}")
        return f"游戏启动失败: {str(e)}"
    finally:
        # 确保资源被释放，即使发生异常
        if 'game' in locals() and hasattr(game, 'cleanup'):
            try:
                game.cleanup()
                print("猜拳游戏资源已清理")
            except Exception as e:
                print(f"清理猜拳游戏资源时出错: {e}")

if __name__ == '__main__':
    main() 