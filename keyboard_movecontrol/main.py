#!/usr/bin/python3
# coding=utf8

"""
键盘控制动作 主程序 V2.0
"""

import sys
import os
import time

# --- 核心依赖库 ---
# 假设 hiwonder 库已按之前的项目结构或方式安装
try:
    # 根据之前的项目结构，添加库的路径
    last_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(last_dir_path)

    import hiwonder.ActionGroupControl as AGC
    from hiwonder.Controller import Controller
    import hiwonder.ros_robot_controller_sdk as rrc
    import hiwonder.yaml_handle as yaml_handle
except ImportError:
    print("\n[错误] 无法导入 hiwonder 库。")
    print("请确保此脚本位于正确的项目目录中，或者 hiwonder 库已正确安装。\n")
    sys.exit(1)

# --- 您提供的动作组字典 ---
# 我们在这里重新整理一下，方便打印菜单
ACTION_GROUPS = {
    '0': ('stand', '立正 (Stand)'),
    '1': ('go_forward', '前进 (Forward)'),
    '2': ('back_fast', '后退 (Back)'),
    '3': ('left_move_fast', '左移 (Move Left)'),
    '4': ('right_move_fast', '右移 (Move Right)'),
    '5': ('push_ups', '俯卧撑 (Push-up)'),
    '6': ('sit_ups', '仰卧起坐 (Sit-up)'),
    '7': ('turn_left', '左转 (Turn Left)'),
    '8': ('turn_right', '右转 (Turn Right)'),
    '9': ('wave', '挥手 (Wave)'),
    '10': ('bow', '鞠躬 (Bow)'),
    '11': ('squat', '下蹲 (Squat)'),
    '12': ('chest', '庆祝 (Celebrate)'),
    '13': ('left_shot_fast', '左脚踢 (Left Kick)'),
    '14': ('right_shot_fast', '右脚踢 (Right Kick)'),
    '15': ('wing_chun', '咏春 (Wing Chun)'),
    '16': ('left_uppercut', '左勾拳 (Left Hook)'),
    '17': ('right_uppercut', '右勾拳 (Right Hook)'),
    '18': ('left_kick', '左侧踢 (Left Side Kick)'),
    '19': ('right_kick', '右侧踢 (Right Side Kick)'),
    '20': ('stand_up_front', '前扑起身 (Stand from Front)'),
    '21': ('stand_up_back', '后倒起身 (Stand from Back)'),
    '22': ('twist', '扭腰 (Twist Waist)'),
    '24': ('stepping', '原地踏步 (March in Place)'),
    '35': ('weightlifting', '举重 (Weightlifting)'),
    '36': ('jiandao','剪刀(Scissor)'),
    '37': ('shitou', '石头(Rock)'),
    '38': ('bu', '布(Paper)'),
    '39': ('cry', '哭泣 (Cry)'),
    '40': ('dance', '跳舞 (Dance)'),
}

def print_menu():
    """打印格式化的动作菜单"""
    print("\n" + "="*40)
    print("--------- 机器人动作菜单 ---------")
    for key, (action, desc) in ACTION_GROUPS.items():
        # 使用 :<5 来左对齐编号，使其更美观
        print(f"  编号 {key:<5} -> {desc}")
    print("="*40)

def main():
    """主函数，包含初始化和主循环"""
    print("--------- 简单控制脚本启动 ---------")
    
    # --- 1. 初始化机器人 ---
    print("[INFO] 正在初始化机器人硬件...")
    try:
        board = rrc.Board()
        controller = Controller(board)
        servo_data = yaml_handle.get_yaml_data(yaml_handle.servo_file_path)
        controller.set_pwm_servo_pulse(1, 1500, 500)
        controller.set_pwm_servo_pulse(2, servo_data['servo2'], 500)
        time.sleep(0.5)
        print("[SUCCESS] 硬件初始化完成。")

        # 让机器人执行站立动作，准备接收指令
        print("[INFO] 机器人站立...")
        AGC.runActionGroup('stand')
        time.sleep(1.5) # 等待站立动作完成
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        return

    # --- 2. 进入主控制循环 ---
    while True:
        print_menu()
        user_input = input("请输入动作编号 (或输入 'q' 退出): ")

        if user_input.lower() == 'q':
            print("[INFO] 收到退出指令，正在关闭...")
            break
        
        if user_input in ACTION_GROUPS:
            action_name, action_desc = ACTION_GROUPS[user_input]
            print(f"\n[EXEC] 正在执行动作: {action_desc}")
            try:
                # 执行指定动作一次
                AGC.runActionGroup(action_name, 1)
                print("[SUCCESS] 动作执行完毕。")
                # 等待一会，让动作有时间完成
                time.sleep(2) 
            except Exception as e:
                print(f"[ERROR] 执行动作 '{action_name}' 时出错: {e}")
        else:
            print("\n[WARNING] 无效的编号，请从菜单中选择。")
            time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # 允许用户通过 Ctrl+C 强制退出
        print("\n[INFO] 检测到 Ctrl+C，强制退出。")
    finally:
        # 确保程序退出时，机器人能有一个结束动作
        print("[INFO] 程序结束，机器人执行立正姿势。")
        try:
            # 即使在初始化失败的情况下也尝试执行，以防万一
            AGC.runActionGroup('stand')
        except:
            pass
