# -*- coding: utf-8 -*-

"""
集成式对话 主程序 V2.0
"""

import time
import sys
import os
import json
from typing import Dict, Any, Optional, List

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
# 添加到上级目录到系统路径中
sys.path.append(parent_dir)

# 拼接模块路径：~/wxzd/large_models_interfaces
module_path = os.path.join(parent_dir, 'large_models_interfaces')

# 添加到Python路径
if module_path not in sys.path:
    sys.path.append(module_path)

# 导入各个模块的接口
try:
    # ASR模块 (关键词识别)
    from utils.asr_vosk import AsrVosk
    
    # Speech2Text模块 (语音转文本)
    from large_models_interfaces.Speech2Text_interface import ParaformerModel
    
    # Text2Speech模块 (文本转语音)
    from large_models_interfaces.Text2Speech_interface import CosyVoiceModel
    
    # LLM Multi-turn模块 (多轮对话)
    from large_models_interfaces.llm_multi_turn_interface import QwenMultiTurnModelInterface

    # 获取设备和采样率
    
    
    # 工具函数接口
    from functions_interface import FUNCTION_MAPPER, TOOLS_DEFINITION
    
    # 工具函数
    from functions_interface import (
        play_rock_paper_scissors,
        execute_action_sequence,
        recognize_scene,
        get_weather_info,
        get_current_time,
        search_web
    )
    
    # 音频播放工具
    from utils.audio import play_wav
    
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块路径正确，且所有依赖已安装。")
    sys.exit(1)


class IntegrateClient:
    """
    集成客户端类
    支持语音多轮对话和Function Calling功能
    """
    
    def __init__(self, system_prompt: Optional[str] = None):
        """
        初始化集成客户端
        
        Args:
            system_prompt: 系统提示词，如果为None则使用默认提示
        """
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # 初始化各个模块实例
        self.asr_instance = None
        self.paraformer_model_instance = None
        self.cosy_voice_model_instance = None
        self.llm_multi_turn_model_instance = None
        
        # 对话状态
        self.conversation_active = False
        
        # 关键词ID
        self.WAKE_UP_ID = 1
        self.GOODBYE_ID = 2
        
        # 初始化所有模块
        self._initialize_modules()
    
    def _get_default_system_prompt(self) -> str:
        """获取默认的系统提示词"""
        return """你是一个智能语音助手机器人，具有以下功能：
1. 可以进行自然的多轮对话
2. 可以调用各种工具函数来帮助用户：
   - 猜拳游戏 (play_rock_paper_scissors)
   - 动作序列执行 (execute_action_sequence)
   - 场景识别 (recognize_scene)
   - 天气查询 (get_weather_info)
   - 时间查询 (get_current_time)
   - 网络搜索 (search_web)

当用户表达猜拳、猜拳游戏石头剪刀布、剪刀石头布或类似意图时，请调用猜拳游戏功能。
当用户表达需要你（机器人）执行动作序列时，请调用动作序列执行功能。
当用户表达需要识别场景、看一下眼前的景色、看看周围环境时，请调用场景识别功能。
当用户需要查询天气时，请调用天气查询功能。
当用户需要查询时间时，请调用时间查询功能。
当用户需要进行网络搜索时，请调用网络搜索功能。
如果用户的意图与工具函数中的意图类似，可能是因为用户表达不清晰，请根据用户意图选择合适的工具函数。
如果用户只是普通对话，请正常回复。
注意：你应该生成纯文本段来描述，不要包含任何特殊符号！"""
    
    def _initialize_modules(self):
        """初始化所有模块"""
        try:

            
            # 添加关键词
            hotwords = {"小新小新": self.WAKE_UP_ID, "再见": self.GOODBYE_ID}
            print(f"ASR模块已准备就绪，监听关键词 '小新小新' (ID:{self.WAKE_UP_ID}) 和 '再见' (ID:{self.GOODBYE_ID})。")
            
            # ASR模块初始化
            self.asr = AsrVosk("../models/vosk-model-small-cn-0.22", hotwords, sample_rate=48000)
            
            # 语音转文本模块初始化
            self.paraformer_model_instance = ParaformerModel()
            print("语音转文本模块已准备就绪。")
            
            # 文本转语音模块初始化
            self.cosy_voice_model_instance = CosyVoiceModel()
            print("文本转语音模块已准备就绪。")
            
            # 多轮对话LLM模块初始化
            self.llm_multi_turn_model_instance = QwenMultiTurnModelInterface(
                initial_system_prompt=self.system_prompt
            )
            print("多轮对话LLM模块已准备就绪。")
            
            # 为LLM添加Function Calling功能
            self._add_function_calling_to_llm()
            print("Function Calling功能已添加。")
            
        except Exception as e:
            print(f"初始化模块时发生错误: {e}")
            print("请检查硬件连接、API Key配置以及所有库是否正确安装。")
            raise
    
    def _execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """
        执行Function Calling
        
        Args:
            function_name: 函数名称
            arguments: 函数参数
            
        Returns:
            str: 执行结果
        """
        try:
            if function_name in FUNCTION_MAPPER:
                function = FUNCTION_MAPPER[function_name]
                if arguments == {}:
                    result = function()
                    return f"工具执行结果：{result}"
                else:                    
                    result = function(arguments)
                    return f"工具执行结果：{result}"
            else:
                return f"错误：未找到函数 {function_name}"
        except Exception as e:
            return f"工具执行出错：{str(e)}"
    
    def _process_llm_response(self, user_input: str) -> str:
        """
        处理LLM响应，使用增强的get_response方法（支持Function Calling）
        
        Args:
            user_input: 用户输入
            
        Returns:
            str: 处理后的响应
        """
        try:
            # 检查LLM实例是否已初始化
            if not self.llm_multi_turn_model_instance:
                print("LLM实例未初始化")
                return "抱歉，系统暂时无法处理您的请求。"
            
            # 直接调用增强的get_response方法（已包含Function Calling）
            return self.llm_multi_turn_model_instance.get_response(user_input)
        except Exception as e:
            print(f"处理LLM响应时发生错误: {e}")
            return "抱歉，处理您的请求时出现了问题。"
    
    def _add_function_calling_to_llm(self):
        """
        为LLM实例添加Function Calling功能，直接复写get_response方法
        """
        if not self.llm_multi_turn_model_instance:
            return
        
        # 保存原始的get_response方法
        original_get_response = self.llm_multi_turn_model_instance.get_response
        
        def enhanced_get_response(user_prompt: str) -> str:
            """
            增强的get_response方法，支持Function Calling
            
            Args:
                user_prompt: 用户输入
                
            Returns:
                str: 处理后的响应
            """
            if not user_prompt:
                return "用户输入不能为空。"
            
            # 检查实例是否有效
            if not self.llm_multi_turn_model_instance:
                return "LLM实例未初始化"
            
            # 将当前用户输入添加到对话历史中
            self.llm_multi_turn_model_instance.messages.append({"role": "user", "content": user_prompt})
            
            try:
                print("正在向通义千问模型发送请求 (多轮对话 with Function Calling)...")
                
                # 调用API with Function Calling
                completion = self.llm_multi_turn_model_instance.client.chat.completions.create(
                    model=self.llm_multi_turn_model_instance.model_name,
                    messages=self.llm_multi_turn_model_instance.messages,  # type: ignore
                    tools=TOOLS_DEFINITION  # type: ignore
                )
                
                response_message = completion.choices[0].message
                
                # 检查是否有工具调用
                if response_message.tool_calls:
                    # 执行工具调用
                    tool_call = response_message.tool_calls[0]
                    function_name = tool_call.function.name
                    arguments_str = tool_call.function.arguments
                    
                    # 解析参数
                    arguments = json.loads(arguments_str)
                    
                    # 执行函数
                    function_result = self._execute_function_call(function_name, arguments)
                    
                    # 将工具调用结果添加到对话历史
                    self.llm_multi_turn_model_instance.messages.extend([
                        {"role": "assistant", "content": "", "tool_calls": response_message.tool_calls},
                        {"role": "tool", "content": function_result, "tool_call_id": tool_call.id}
                    ])
                    
                    # 工具函数已经处理完所有回复逻辑，播放任务完成音频
                    final_response = "还有什么我可以帮你的吗？"
                    
                    # 播放任务完成音频文件
                    wav_path = os.path.join(current_dir, "任务完成.wav")
                    if os.path.exists(wav_path):
                        play_wav(wav_path)
                        return ''
                    else:
                        print(f"警告：找不到音频文件 {wav_path}")
                        # 如果找不到音频文件，则使用TTS播放
                        if self.cosy_voice_model_instance:
                            self.cosy_voice_model_instance.text2speech(final_response)
                    
                    # 更新对话历史
                    self.llm_multi_turn_model_instance.messages.append({"role": "assistant", "content": final_response})
                    
                    return final_response
                else:
                    # 没有工具调用，直接返回回复
                    response_content = response_message.content
                    
                    # 更新对话历史
                    self.llm_multi_turn_model_instance.messages.append({"role": "assistant", "content": response_content.strip() if response_content else ""})
                    
                    return response_content.strip() if response_content else "抱歉，没有收到有效回复"
                    
            except Exception as e:
                error_message = f"Function Calling调用失败: {e}"
                print(error_message)
                # 如果Function Calling失败，降级到原始方法
                return original_get_response(user_prompt)
        
        # 直接复写get_response方法
        self.llm_multi_turn_model_instance.get_response = enhanced_get_response
    
    def start_conversation(self):
        """开始语音对话"""
        print("程序启动。")
        print("\n--- 进入主循环 ---")
        
        conversation_num = 0
        
        
        while True:
            try:
                if not self.conversation_active:
                    # 阶段1: 监听唤醒关键词或结束关键词
                    print("\r[主循环] 正在监听唤醒词 '小新小新' 或结束词 '再见'...", end="", flush=True)
                    command_id = self.asr.listen_for_hotword()
                    
                    if command_id == self.WAKE_UP_ID:
                        print("\n检测到关键词 '小新小新'。")
                        play_wav("我在.wav")
                        self.conversation_active = True
                        print("进入对话模式。")
                        # 重置LLM对话历史
                        #self.llm_multi_turn_model_instance.reset_conversation()
                        
                    elif command_id == self.GOODBYE_ID:
                        print("\n检测到关键词 '再见'，程序将结束。")
                        if self.cosy_voice_model_instance:
                            self.cosy_voice_model_instance.text2speech("再见，期待下次与你对话。")
                        
                        # 执行站立动作
                        try:
                            # 导入ActionGroupControl模块
                            sys.path.append('/home/pi/TonyPi/')
                            import hiwonder.ActionGroupControl as AGC
                            
                            # 执行站立动作
                            AGC.runActionGroup('stand')
                            print("机器人姿态已恢复")
                        except Exception as e:
                            print(f"恢复机器人姿态时出错: {e}")
                            
                        break
                    
                    time.sleep(0.1)
                    
                else:
                    # 阶段2: 对话模式
                    print("\n[对话模式] 正在等待您的语音输入...")
                    user_input_text = self.paraformer_model_instance.speech2text()
                    print(f"[对话模式] 识别到用户语音: '{user_input_text}'")
                    
                    # 检查是否要结束对话
                    #if "再见" in user_input_text:
                        #print("检测到语音输入 '再见'，结束当前对话。")
                        #response_text = self._process_llm_response(user_input_text)
                        #print(f"[对话模式] LLM回复: '{response_text}'")
                        #if self.cosy_voice_model_instance:
                         #   self.cosy_voice_model_instance.text2speech(response_text)
                        
                        #self.conversation_active = False
                        #self.llm_multi_turn_model_instance.reset_conversation()
                        #self.asr_instance.getResult()
                        #continue
                    
                    # 检查输入是否为空
                    if not user_input_text.strip():
                        print("没有检测到有效语音输入，请再说一遍。")
                        if self.cosy_voice_model_instance:
                            self.cosy_voice_model_instance.text2speech("没有检测到有效语音输入，请再说一遍。")
                        continue
                    
                    conversation_num +=1
                    
                    self.conversation_active = False
                    # 处理用户输入
                    response_text = self._process_llm_response(user_input_text)
                    print(f"[对话模式] 回复: '{response_text}'")
                    
                    # 文本转语音并播放
                    if self.cosy_voice_model_instance and response_text != '':
                        self.cosy_voice_model_instance.text2speech(response_text)
                        
                    # 每10次对话清除历史
                    if (conversation_num + 1) % 10 == 0:
                        self.llm_multi_turn_model_instance.reset_conversation()
                    
            except Exception as e:
                print(f"主循环中发生错误: {e}")
                self.conversation_active = False
                if self.llm_multi_turn_model_instance:
                    self.llm_multi_turn_model_instance.reset_conversation()
                time.sleep(1)
        
        print("程序结束。")
    
    def stop(self):
        """停止客户端"""
        print("正在停止客户端...")
        
        # 执行站立动作
        try:
            # 导入ActionGroupControl模块
            sys.path.append('/home/pi/TonyPi/')
            import hiwonder.ActionGroupControl as AGC
            
            # 执行站立动作
            AGC.runActionGroup('stand')
            print("机器人姿态已恢复")
        except Exception as e:
            print(f"恢复机器人姿态时出错: {e}")
            
        # 清理资源
        print("客户端已停止。")


def main():
    """主函数"""
    try:
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
        
        # 创建集成客户端实例
        client = IntegrateClient()
        
        # 开始对话
        client.start_conversation()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断。")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 恢复stderr
        if 'stderr_fd' in locals():
            os.dup2(stderr_fd, 2)
        if 'devnull' in locals():
            devnull.close()
        if 'client' in locals():
            client.stop()


if __name__ == "__main__":
    main() 