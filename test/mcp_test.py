"""
MCP接口 测试脚本 V2.0
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from large_models_interfaces.mcp_interface import MCPModel

# 设置阿里云应用app_id
app_id = ''

# 实例化model
mcpModel = MCPModel(app_id=app_id, system_prompt='返回纯文本', memory=True)

text1='我想知道武汉今天的天气'

# 调用接口
response_text = mcpModel.get_response(text1)

print(response_text)

text2='从武汉理工大学到黄鹤楼应该怎么公共出行，请根据今天天气规划路线'

# 调用接口
response_text = mcpModel.get_response(text2)

print(response_text)
