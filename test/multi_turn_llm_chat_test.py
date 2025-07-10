"""
多轮对话接口 测试脚本 V2.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. 导入多轮对话接口
# 假设 llm_multi_turn_interface.py 在 large_models_interfaces 目录下
from large_models_interfaces.llm_multi_turn_interface import QwenMultiTurnModelInterface

# 2. 定义系统提示词 (可选，如果不提供则使用默认通用助手提示)
my_system_prompt = "你是一个友好的AI助手，请用简洁的语言回答问题。"

# 3. 初始化多轮对话接口
# 可以指定模型名称，默认为 "qwen-plus"
llm_chat = QwenMultiTurnModelInterface(model="qwen-plus", initial_system_prompt=my_system_prompt)

print("--- 开始多轮对话 (输入'退出'结束) ---")

while True:
    user_input = input("你: ")
    if user_input.lower() == '退出':
        break

    # 4. 调用 get_response 方法获取模型回复
    # 该方法会自动维护对话历史
    model_response = llm_chat.get_response(user_prompt=user_input)

    # 5. 打印模型回复
    print(f"AI: {model_response}")

print("\n--- 对话结束 ---")

# 6. (可选) 打印完整的对话历史
print("\n--- 完整对话历史记录 ---")
for message in llm_chat.get_conversation_history():
    print(f"[{message['role']}]: {message['content']}")

# 7. (可选) 重置对话历史，开始新的对话
# llm_chat.reset_conversation(new_system_prompt="你现在是一个美食推荐专家。")
# print("\n--- 对话历史已重置，开始新的美食对话 ---")
# print(f"AI: {llm_chat.get_response(user_prompt='你好，我想吃点好吃的。')}")
