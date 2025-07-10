"""
单轮对话接口 测试脚本 V2.0
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 1. 导入该文件的QwenModelInterface接口
from large_models_interfaces.llm_single_turn_interface import QwenModelInterface

# 2. 初始化接口
llm = QwenModelInterface(model="qwen-plus")

# 3. 定义输入信息和系统提示词
user_prompt = input("请输入用户输入:")
system_prompt = "你是一个幽默风趣的AI助手，喜欢结束的时候讲个笑话"

# 4. 调用get_response, 获得结果
answer = llm.get_response(user_prompt, system_prompt)

# 5. 打印结果
print(f"\n[用户问题]: {user_prompt}")
print(f"[模型回答]: {answer}")
