"""
语音转文本接口 测试脚本 V2.0
"""

import sys
import os
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
    
# 导入模块
from large_models_interfaces.Speech2Text_interface import ParaformerModel

# 初始化模型
ParaformerModel = ParaformerModel()

# 运行模型
text = ParaformerModel.speech2text()

print(text)