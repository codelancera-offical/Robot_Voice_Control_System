# -*- coding: utf-8 -*-

"""
Function Calling接口 V2.0
核心功能是实现Function Calling接口，从而连接大模型与工具函数。
"""

import random
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from large_models_interfaces.Text2Speech_interface import CosyVoiceModel
from utils.audio import play_wav

# 获取当前脚本所在目录的路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 音频文件路径
LET_ME_SEE_WAV = os.path.join(CURRENT_DIR, "让我看看.wav")

# 获取当前脚本文件所在的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取当前脚本所在文件夹的上级目录路径
parent_dir = os.path.dirname(current_dir)

# 将上级目录添加到 Python 的模块搜索路径中。
# 这样，位于该上级目录下的子文件夹（作为包）中的模块，就可以通过 `子文件夹名.模块名` 的形式直接导入了。
sys.path.append(parent_dir)

# 添加rps模块路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rps'))

# 不再需要预先导入RPSGame，因为我们将在函数内部直接导入main



def play_rock_paper_scissors(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    猜拳游戏工具函数
    
    Args:
        arguments: 可选参数，目前未使用
            
    Returns:
        str: 游戏结果字符串
    """
    print("Function Calling: play_rock_paper_scissors")
    game = None
    try:
        # 直接导入RPSGame类
        from rps.rps_game import RPSGame
        
        print("启动石头剪刀布游戏...")
        
        # 创建游戏实例并调用play_one_round方法
        game = RPSGame()
        game.play_one_round()
        
        return "石头剪刀布游戏已完成"
    except Exception as e:
        print(f"启动石头剪刀布游戏失败: {e}")
        return f"游戏启动失败: {str(e)}"
    finally:
        # 确保资源被释放，即使发生异常
        if game is not None and hasattr(game, 'cleanup'):
            try:
                game.cleanup()
                print("猜拳游戏资源已清理")
            except Exception as e:
                print(f"清理猜拳游戏资源时出错: {e}")


def execute_action_sequence(arguments: Optional[Dict[str, Any]]):
    """
    动作序列执行工具函数
    
    Returns:
        str: 执行结果字符串，格式为："已执行动作序列：{动作列表}，执行完成。"
    """
    print("Function Calling: execute_action_sequence")
    
    # 延迟导入，避免导入时机问题
    try:
        # 动态添加路径
        import sys
        import os
        
        # 使用完整的模块路径导入
        import action_seq.main as action_seq_main
        request_text = arguments.get('request_text', '') if arguments else ''
        controller = action_seq_main.ActionSequenceController(play_wav=False)
        controller.run_once(request_text=request_text)
        return f"动作序列已执行完毕，执行结果：{request_text}"
    except Exception as e:
        print(f"执行动作序列时出错: {e}")
        return f"动作序列执行失败: {str(e)}"


def recognize_scene(arguments: Optional[Dict[str, Any]] = None) -> str:
    """
    场景识别工具函数
    
    Args:
        arguments: 可选参数，目前未使用
            
    Returns:
        str: 识别结果字符串，描述场景内容
    """
    print("Function Calling: recognize_scene")
    
    try:
        # 添加VLM模块路径
        import sys
        import os
        vlm_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'vlm')
        if vlm_path not in sys.path:
            sys.path.insert(0, vlm_path)
        
        # 导入语音识别类
        from vlm.voice_recognition import VoiceRecognition
        
        # 创建语音识别器实例
        voice_recognizer = VoiceRecognition()
        
        try:
            print("正在执行场景识别...")
            # 直接调用recognize_image方法
            voice_recognizer.recognize_image()
            return "场景识别已完成，结果已通过语音播报"
        finally:
            # 确保资源被释放
            if hasattr(voice_recognizer, 'cleanup') and callable(voice_recognizer.cleanup):
                voice_recognizer.cleanup()
        
    except Exception as e:
        print(f"场景识别失败: {e}")
        import traceback
        traceback.print_exc()
        return f"场景识别出错: {str(e)}"


def get_weather_info(arguments: Optional[Dict[str, Any]]) -> str:
    """
    天气查询工具函数
    
    Returns:
        str: 天气信息字符串，格式为："{地点}的天气：{天气状况}，温度{温度}°C，{其他信息}"
    """
    print("Function call: get_weather_info")
    
    # 播放"让我看看"音频
    if os.path.exists(LET_ME_SEE_WAV):
        print("播放'让我看看'音频...")
        play_wav(LET_ME_SEE_WAV)
    else:
        print(f"警告：找不到音频文件 {LET_ME_SEE_WAV}")
    
    from large_models_interfaces.mcp_interface import MCPModel
    mcp_model = MCPModel(app_id='', system_prompt='', memory=True)
    response_text = mcp_model.get_response(arguments['query'])
    print(arguments['query'])
    print(response_text)
    # 读出来
    try:
        tts = CosyVoiceModel()
        tts.text2speech(response_text)
        return response_text
    except Exception as e:
        return f"获取天气并朗读时出错：{e}"



def get_current_time():
    print("Function call: get_current_time")
    print("获取当前时间")
    now = datetime.now()
    time_str = now.strftime("当前时间为%Y年%m月%d日 %H时%M分%S秒")
    try:
        tts = CosyVoiceModel()
        tts.text2speech(time_str)
        return time_str
    except Exception as e:
        return f"获取时间并朗读时出错：{e}"

def search_web(arguments: Optional[Dict[str, Any]]):
    """
    联网搜索工具函数
    
    Returns:
        str: 搜索"{关键词}"的结果：{搜索结果摘要}"
    """
    print("Function call: search_web")
    
    # 播放"让我看看"音频
    if os.path.exists(LET_ME_SEE_WAV):
        print("播放'让我看看'音频...")
        play_wav(LET_ME_SEE_WAV)
    else:
        print(f"警告：找不到音频文件 {LET_ME_SEE_WAV}")
    
    from large_models_interfaces.mcp_interface import MCPModel
    mcp_model = MCPModel(app_id='', system_prompt='', memory=True)
    response_text = mcp_model.get_response(arguments['query'])
    print(arguments['query'])
    print(response_text)
    # 读出来
    try:
        tts = CosyVoiceModel()
        tts.text2speech(response_text)
        return response_text
    except Exception as e:
        return f"获取结果并朗读时出错：{e}"


# 工具函数映射表，用于Function Calling
FUNCTION_MAPPER = {
    "play_rock_paper_scissors": play_rock_paper_scissors,
    "execute_action_sequence": execute_action_sequence,
    "recognize_scene": recognize_scene,
    "get_weather_info": get_weather_info,
    "get_current_time": get_current_time,
    "search_web": search_web
}


# Function Calling所需的tools数组定义
TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "play_rock_paper_scissors",
            "description": "当用户想要玩猜拳或猜拳游戏或石头剪刀布或剪刀石头布时使用，可以与用户进行猜拳和石头剪刀布游戏。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_action_sequence",
            "description": "当用户需要执行一系列动作时使用，可以控制机器人或虚拟角色执行动作序列。",
            "parameters": {
                "type": "object",
                "properties": {
                    "request_text":{
                        "type": "string",
                        "description": "一句完成的自然语言描述的动作序列，如先跳舞，再摆腰，最后鞠躬。"
                    }
                },
                "required": ["request_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recognize_scene",
            "description": "当用户需要识别场景或环境时使用，可以分析场景描述或图片内容。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_info",
            "description": "当用户查询天气信息时使用，可以获取指定地区的天气状况。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":{
                        "type": "string",
                        "description": "一句完成的自然语言天气查询：比如，深圳福田今天的天气"
                    }
                },
                "required": ["query"]
            } # 已修改
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "当用户询问当前时间时使用，可以获取当前的日期和时间信息。",
            "parameters": {} # 已修改
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "当用户需要搜索网络信息，或者直接说明需要联网搜索时使用，可以在互联网上搜索相关信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":{
                        "type": "string",
                        "description": "一句完成的自然语言查询：比如，联网搜索最近的新闻，或者搜索最近的新闻"
                    }
                },
                "required": ["query"]
            } # 已修改
        }
    }
]


if __name__ == "__main__":
    # 测试工具函数定义
    print("工具函数接口定义测试：")
    print(f"定义了 {len(FUNCTION_MAPPER)} 个工具函数：")
    for func_name in FUNCTION_MAPPER.keys():
        print(f"- {func_name}")
    
    print(f"\nTOOLS_DEFINITION 包含 {len(TOOLS_DEFINITION)} 个工具定义")
    print("工具函数接口定义完成！")