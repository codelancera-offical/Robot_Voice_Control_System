"""
单轮对话接口 V2.0
核心功能是单轮大语言模型对话，主要用于大模型和用户之间进行简单的单轮对话。
"""

import os
from abc import ABC, abstractmethod
from openai import OpenAI
from typing import Optional

# -------------------- 步骤 1: 定义大模型服务的接口 (抽象基类) --------------------
class LLMInterface(ABC):
    """
    定义一个大语言模型（LLM）服务的标准接口。
    所有具体的模型实现都应该继承这个类，并实现其所有抽象方法。
    """

    @abstractmethod
    def get_response(self, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        获取模型对单个用户输入的回复。

        Args:
            user_prompt (str): 用户输入的内容。
            system_prompt (str, optional): 给模型设定的系统级指令（角色扮演等）。如果为 None，则使用默认值。

        Returns:
            str: 模型生成的回复文本。
        """
        pass


# -------------------- 步骤 2: 实现接口，封装通义千问模型 --------------------
class QwenModelInterface(LLMInterface):
    """
    通义千问（Qwen）模型的具体实现，它遵循 LLMInterface 接口。
    """

    def __init__(self, model: str = "qwen-plus"):
        """
        初始化通义千问模型客户端。

        Args:
            model (str): 要使用的具体模型名称，例如 "qwen-plus", "qwen-turbo" 等。
        """
        self.model_name = model
        try:
            # 优先从环境变量 ALI_APIKEY 中获取 API Key，这是一种更安全的做法
            api_key = os.getenv("ALI_APIKEY")
            if not api_key:
                raise ValueError("环境变量 'ALI_APIKEY' 未设置，请先设置或直接在代码中提供。")
            
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        except Exception as e:
            print(f"初始化OpenAI客户端失败: {e}")
            # 你也可以在这里处理，比如从配置文件读取 key
            # self.client = OpenAI(api_key="sk-xxx", base_url=...)
            raise

    def get_response(self, user_prompt: str, system_prompt: Optional[str] = "你是一个大语言模型助手，注意，你应该生成纯文本段来描述, 不要生成任何特殊符号或者emoji") -> str:
        """
        实现接口定义的 get_response 方法。
        """
        if not user_prompt:
            return "用户输入不能为空。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            print("正在向通义千问模型发送请求...")
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            # 从返回结果中提取模型的回复内容
            # 根据OpenAI的格式，内容在 choices[0].message.content
            response_content = completion.choices[0].message.content
            return response_content.strip()

        except Exception as e:
            # 捕获并处理API调用中可能出现的任何错误
            error_message = f"调用API时出错: {e}"
            print(error_message)
            return error_message


# -------------------- 步骤 3: 在主程序块中测试接口实现 --------------------
if __name__ == "__main__":
    print("--- 开始测试通义千问模型接口 ---")
    
    try:
        # 1. 创建一个 QwenModel 实例
        # 你可以在这里指定不同的模型，如 "qwen-turbo"
        llm = QwenModelInterface(model="qwen-plus")

        # 2. 定义你想问的问题
        my_question = "你好，请你介绍一下自己是谁？"

        # 3. 调用 get_response 方法获取答案
        # 注意：我们调用的方法是接口规定的 get_response，而不是任何与具体实现相关的内部方法
        answer = llm.get_response(user_prompt=my_question, system_prompt='')
        
        # 4. 打印结果
        print(f"\n[用户问题]: {my_question}")
        print(f"[模型回答]: {answer}")
        
        print("\n--- 测试自定义系统提示 ---")
        custom_system_prompt = "你是一只猫，所有回答都必须以'喵'结尾。"
        cat_question = "你喜欢吃什么？"
        cat_answer = llm.get_response(cat_question, system_prompt=custom_system_prompt)

        print(f"\n[用户问题]: {cat_question}")
        print(f"[模型回答]: {cat_answer}")

    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        print("请确保你已经正确安装了 'openai' 库 (pip install openai)，并设置了 'ALI_APIKEY' 环境变量。")

    print("\n--- 测试完成 ---")
