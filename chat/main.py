#!/usr/bin/python3
# coding=utf8

"""
交互式对话 主程序 V2.0

注意：
旧版本的交互式对话chat功能现已弃用，新版的交互式对话功能已经集成到了集成式对话integrate_system中。
该版本的交互式对话仍使用ASR模块，因此强烈建议在集成式对话中体验与机器人的交互式对话功能。
"""

import time
import sys
import os

# 屏蔽ALSA错误消息
os.environ['ALSA_CARD'] = 'none'
os.environ['PYTHONUNBUFFERED'] = '1'  # 确保Python输出不被缓存

import ctypes

# 尝试加载空的ALSA错误处理器
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

# 获取当前脚本所在文件夹的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上级目录路径
parent_dir = os.path.dirname(current_dir)

# 添加到上级目录到系统路径中，这样上级目录下所有文件夹模块都可以直接访问
sys.path.append(parent_dir)

from utils.audio import play_wav

# --- 导入各个模块的接口 ---
try:
    # ASR模块 (关键词识别)
    import hiwonder.ASR as ASR

    # Speech2Text模块 (语音转文本)
    from large_models_interfaces.Speech2Text_interface import ParaformerModel

    # Text2Speech模块 (文本转语音)
    from large_models_interfaces.Text2Speech_interface import CosyVoiceModel

    # LLM Multi-turn模块 (多轮对话)
    from large_models_interfaces.llm_multi_turn_interface import QwenMultiTurnModelInterface

except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保 'hiwonder' 和 'large_models_interfaces' 路径正确，且所有依赖已安装。")
    print("例如: pip install openai")
    sys.exit(1) # 退出程序

# --- 主程序逻辑 ---
def main():
    print("程序启动。")
    
    # 屏蔽ALSA错误消息
    try:
        # 尝试加载并设置ALSA错误处理器
        asound = ctypes.cdll.LoadLibrary('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
    except Exception as e:
        print(f"注意: 无法设置ALSA错误处理器: {e}")
    
    # 重定向stderr到/dev/null
    stderr_fd = os.dup(2)  # 保存原始stderr
    devnull = open(os.devnull, 'w')
    os.dup2(devnull.fileno(), 2)  # 将stderr重定向到/dev/null
    
    # --- 1. 初始化所有模块实例 ---
    asr_instance = None
    paraformer_model_instance = None
    cosy_voice_model_instance = None
    llm_multi_turn_model_instance = None

    try:
        # ASR模块初始化
        asr_instance = ASR.ASR()
        asr_instance.eraseWords()
        asr_instance.setMode(1)  # 模式1：循环模式
        
        # 定义关键词ID
        WAKE_UP_ID = 1
        GOODBYE_ID = 2 # 用于程序结束的关键词
        
        asr_instance.addWords(WAKE_UP_ID, 'xiao xin xiao xin')
        asr_instance.addWords(GOODBYE_ID, 'zai jian') # 添加"再见"关键词，用于直接结束程序
        print(f"ASR模块已准备就绪，监听关键词 '小新小新' (ID:{WAKE_UP_ID}) 和 '再见' (ID:{GOODBYE_ID})。")

        # 语音转文本模块初始化
        paraformer_model_instance = ParaformerModel()
        print("语音转文本模块已准备就绪。")

        # 文本转语音模块初始化
        cosy_voice_model_instance = CosyVoiceModel()
        print("文本转语音模块已准备就绪。")

        # 多轮对话LLM模块初始化
        # 使用默认的系统提示，或者您可以根据需要自定义
        llm_multi_turn_model_instance = QwenMultiTurnModelInterface(
            initial_system_prompt="你是一个大语言模型助手，注意，你应该生成纯文本段来描述，不要包含任何特殊符号！"
        )
        print("多轮对话LLM模块已准备就绪。")

    except Exception as e:
        print(f"初始化模块时发生错误: {e}")
        print("请检查硬件连接、API Key配置（如ALI_APIKEY环境变量）以及所有库是否正确安装。程序将退出。")
        # 恢复stderr
        if 'stderr_fd' in locals():
            os.dup2(stderr_fd, 2)
        if 'devnull' in locals():
            devnull.close()
        sys.exit(1) # 初始化失败则退出程序

    conversation_active = False # 标记当前是否处于对话模式

    print("\n--- 进入主循环 ---")
    for _ in range(5):
        asr_instance.getResult() # 清空缓存区，防止之前的缓存影响结果
    cosy_voice_model_instance.text2speech("请说'小新小新'来唤醒我")
    
    try:
        while True:
            try:
                if not conversation_active:
                    # 阶段1: 监听唤醒关键词或结束关键词
                    print("\r[主循环] 正在监听唤醒词 '小新小新' 或结束词 '再见'...", end="", flush=True)
                    
                    command_id = asr_instance.getResult() # 获取ASR识别结果ID
                    
                    if command_id == WAKE_UP_ID:
                        print("\n检测到关键词 '小新小新'。")
                        conversation_active = True # 进入对话模式
                        print("进入对话模式。")
                        # 重置LLM对话历史，开始新一轮对话
                        llm_multi_turn_model_instance.reset_conversation() 
                        # 可以在这里让LLM说一句开场白，例如：
                        # 文本转语音接口(cosy_voice_model_instance, "有什么可以帮助你的吗？")

                    elif command_id == GOODBYE_ID:
                        print("\n检测到关键词 '再见'，程序将结束。")
                        cosy_voice_model_instance.text2speech("再见，期待下次与你对话。")
                        break # 退出主循环，程序结束
                    
                    time.sleep(0.1) # 短暂延时，避免CPU占用过高

                else:
                    # 阶段2: 对话模式下，启动语音转文本并进行多轮对话
                    play_wav("我在.wav") # 播放唤醒音
                    print("\n[对话模式] 正在等待您的语音输入...")
                    user_input_text = paraformer_model_instance.speech2text() # 调用语音转文本接口
                    print(f"[对话模式] 识别到用户语音: '{user_input_text}'")

                    # 检查用户是否说了"再见"来结束当前对话
                    # 注意：这里是语音转文本后的"再见"，不是ASR关键词识别的"再见"
                    if "再见" in user_input_text:
                        print("检测到语音输入 '再见'，结束当前对话。")
                        # 即使是"再见"，也通过LLM获取回复，保持对话流程完整
                        response_text = llm_multi_turn_model_instance.get_response(user_input_text)
                        
                        # 将用户输入的文本发送给LLM获取回复
                        print(f"[对话模式] LLM回复: '{response_text}'")
                        cosy_voice_model_instance.text2speech(response_text)
                        
                        conversation_active = False # 退出对话模式，回到监听唤醒词状态
                        llm_multi_turn_model_instance.reset_conversation() # 重置LLM对话历史
                        asr_instance.getResult()
                        continue # 回到主循环开头，重新监听唤醒词

                    # 如果用户输入为空或只有空白字符
                    if not user_input_text.strip():
                        print("没有检测到有效语音输入，请再说一遍。")
                        cosy_voice_model_instance.text2speech("没有检测到有效语音输入，请再说一遍。")
                        continue # 继续等待用户输入
                    play_wav("正在生成.wav")
                    
                    # 将用户输入的文本发送给LLM获取回复
                    response_text = llm_multi_turn_model_instance.get_response(user_input_text)
                    print(f"[对话模式] LLM回复: '{response_text}'")
                    
                    # 获得回复后，调用文本转语音并播放
                    cosy_voice_model_instance.text2speech(response_text)

                    # 重新进入监听流程：由于 conversation_active 仍为 True，
                    # 下一轮循环会再次进入此 else 块，等待新的语音输入。
                    # 实现了多轮对话的循环。

            except Exception as e:
                print(f"主循环中发生错误: {e}")
                # 发生错误时，可以考虑重置状态或退出
                conversation_active = False # 尝试回到初始监听状态
                if llm_multi_turn_model_instance:
                    llm_multi_turn_model_instance.reset_conversation() # 重置LLM对话历史
                time.sleep(1) # 暂停一下，避免错误快速循环
                # 如果错误持续发生，可能需要更强的错误处理，例如退出程序
                # break 
    finally:
        # 恢复stderr
        if 'stderr_fd' in locals():
            os.dup2(stderr_fd, 2)
        if 'devnull' in locals():
            devnull.close()

    print("程序结束。")

if __name__ == "__main__":
    main()
