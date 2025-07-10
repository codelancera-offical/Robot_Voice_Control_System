#!/usr/bin/python3
# coding=utf8

"""
键盘监控工具 V2.0
核心功能是监控键盘输入，主要用于在机器人运行时实现键盘控制。
"""

import sys
import select
import termios
import tty

class KeyboardMonitor:
    """键盘监控：负责检测键盘输入"""
    
    def __init__(self):
        """初始化键盘监控器"""
        self.old_settings = None
        self.setup_terminal()
    
    def setup_terminal(self):
        """设置终端为非阻塞输入模式"""
        try:
            # 保存终端原始设置
            self.old_settings = termios.tcgetattr(sys.stdin)
            # 设置终端为非规范模式
            tty.setcbreak(sys.stdin.fileno())
        except Exception as e:
            print(f"键盘监控：设置终端模式失败: {e}")
            print("键盘监控：键盘输入功能将不可用")
            self.old_settings = None
    
    def restore_terminal(self):
        """恢复终端原始设置"""
        if self.old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except Exception as e:
                print(f"键盘监控：恢复终端模式失败: {e}")
    
    def is_enter_pressed(self):
        """检测是否按下回车键
        
        Returns:
            bool: 如果按下回车键返回True，否则返回False
        """
        if not self.old_settings:
            return False
            
        # 检测是否有输入
        rlist, _, _ = select.select([sys.stdin], [], [], 0)
        if rlist:
            key = sys.stdin.read(1)
            # 回车键的ASCII码是13或10
            return key == '\n' or key == '\r'
        return False 