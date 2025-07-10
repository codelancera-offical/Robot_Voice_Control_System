"""
多轮对话接口 V2.0
核心功能是多轮大模型交互对话，主要用于大模型和用户之间进行多轮的交互式对话。
"""

import os
from typing import Optional
# 假设 llm_single_turn_interface.py 在 large_models_interfaces 目录下
# 如果不在，请根据实际路径调整导入语句
from .llm_single_turn_interface import QwenModelInterface
import sys

print(f"Python sys.stdin.encoding: {sys.stdin.encoding}")

class QwenMultiTurnModelInterface(QwenModelInterface):
    """
    通义千问（Qwen）模型的多轮对话实现，继承自 QwenModelInterface。
    该类维护一个内部的对话历史列表，以支持连续对话。
    """

    def __init__(self, model: str = "qwen-plus", initial_system_prompt: Optional[str] = None):
        """
        初始化多轮对话模型客户端。

        Args:
            model (str): 要使用的具体模型名称，例如 "qwen-plus", "qwen-turbo" 等。
            initial_system_prompt (str, optional): 对话开始时设定的系统级指令。
                                                    如果为 None，则使用默认的通用助手提示。
        """
        super().__init__(model=model)
        self.messages = []
        # 初始化对话历史，添加系统提示
        if initial_system_prompt:
            self.messages.append({"role": "system", "content": initial_system_prompt})
        else:
            # 默认的系统提示，与单轮对话接口中的默认值保持一致
            self.messages.append({"role": "system", "content": "你是一个大语言模型助手，注意，你应该生成纯文本段来描述，不要包含任何特殊符号！"})

    def get_response(self, user_prompt: str) -> str:
        """
        获取模型对多轮对话中单个用户输入的回复，并维护对话历史。

        Args:
            user_prompt (str): 用户输入的内容。

        Returns:
            str: 模型生成的回复文本。
        """
        if not user_prompt:
            return "用户输入不能为空。"

        # 将当前用户输入添加到对话历史中
        
        self.messages.append({"role": "user", "content": user_prompt})
        #print("messages", self.messages)
        # --- 添加以下调试打印 ---
        #print(f"DEBUG: user_prompt (repr): {repr(user_prompt)}")
        #print(f"DEBUG: messages (repr): {repr(self.messages)}")
        # --- 调试打印结束 ---
        
        try:
            print("正在向通义千问模型发送请求 (多轮对话)...")
            # 调用父类的客户端进行API请求，传入完整的对话历史
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages, # 使用累积的对话历史列表
            )
            response_content = completion.choices[0].message.content
            
            # 将模型的回复添加到对话历史中
            self.messages.append({"role": "assistant", "content": response_content.strip() if response_content else ""})
            
            return response_content.strip() if response_content else ""

        except Exception as e:
            error_message = f"调用API时出错: {e}"
            print(error_message)
            # 如果API调用失败，为了避免后续对话受损，可以考虑移除最后一条用户消息
            # 但这里为了简单，直接返回错误信息
            return error_message

    def reset_conversation(self, new_system_prompt: Optional[str] = None):
        """
        重置对话历史，可以选择设置新的系统提示。
        这对于开始一个全新的对话非常有用。
        """
        self.messages = []
        if new_system_prompt:
            self.messages.append({"role": "system", "content": new_system_prompt})
        else:
            # 如果没有提供新的系统提示，则使用默认的通用助手提示
            self.messages.append({"role": "system", "content": "你是一个大语言模型助手，注意，你应该生成纯文本段来描述，不要包含任何特殊符号！"})
        print("对话历史已重置。")

    def get_conversation_history(self) -> list:
        """
        获取当前的完整对话历史列表。
        """
        return self.messages

# -------------------- 测试多轮对话接口实现 --------------------
if __name__ == "__main__":
    print("--- 开始测试通义千问多轮对话模型接口 ---")
    
    # 示例：使用您提供的手机商店系统提示
    phone_shop_system_prompt = """你是一名阿里云百炼手机商店的店员，你负责给用户推荐手机。手机有两个参数：屏幕尺寸（包括6.1英寸、6.5英寸、6.7英寸）、分辨率（包括2K、4K）。
        你一次只能向用户提问一个参数。如果用户提供的信息不全，你需要反问他，让他提供没有提供的参数。如果参数收集完成，你要说：我已了解您的购买意向，请稍等。"""

    try:
        # 1. 创建一个 QwenMultiTurnModelInterface 实例
        # 传入手机商店的系统提示
        llm_multi_turn = QwenMultiTurnModelInterface(
            model="qwen-plus", 
            initial_system_prompt=phone_shop_system_prompt
        )

        # 2. 进行多轮对话
        print("\n--- 手机商店对话示例 ---")
        
        # 第一轮：模型应该根据系统提示开始对话
        # 注意：这里我们没有一个初始的“模型输出”，因为系统提示是给模型的，不是模型主动说的
        # 我们可以模拟第一句模型输出，或者让用户先提问
        # 为了符合您提供的参考代码的流程，我们让用户先输入
        
        # 模拟参考代码中的第一句模型输出
        assistant_output_initial = "欢迎光临阿里云百炼手机商店，您需要购买什么尺寸的手机呢？"
        print(f"模型输出：{assistant_output_initial}\n")
        # 将这句模拟的输出也加入到对话历史中，以便模型知道它“说过”这句话
        llm_multi_turn.messages.append({"role": "assistant", "content": assistant_output_initial})


        while True:
            user_input = input("请输入 (输入'退出'结束): ")
            if user_input.lower() == '退出':
                break
            
            answer = llm_multi_turn.get_response(user_prompt=user_input)
            
            print(f"\n[用户问题]: {user_input}")
            print(f"[模型回答]: {answer}")
            
            if "我已了解您的购买意向" in answer:
                print("\n模型已收集到足够信息，对话结束。")
                break

        # 3. 打印完整的对话历史（可选）
        print("\n--- 完整对话历史 ---")
        for msg in llm_multi_turn.get_conversation_history():
            print(f"[{msg['role']}]: {msg['content']}")

        # 4. 测试重置对话
        print("\n--- 测试重置对话 ---")
        llm_multi_turn.reset_conversation(new_system_prompt="你是一个友好的AI助手。")
        first_question_after_reset = "你好，你叫什么名字？"
        reset_answer = llm_multi_turn.get_response(user_prompt=first_question_after_reset)
        print(f"\n[用户问题]: {first_question_after_reset}")
        print(f"[模型回答]: {reset_answer}")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        print("请确保你已经正确安装了 'openai' 库 (pip install openai)，并设置了 'ALI_APIKEY' 环境变量。")

    print("\n--- 测试完成 ---")
