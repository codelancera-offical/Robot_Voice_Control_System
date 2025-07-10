#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音控制动作 大语言模型处理器模块 V2.0
"""

import os
import sys
import json
from typing import Dict, List, Union, Optional

# 屏蔽ALSA错误消息
os.environ['ALSA_CARD'] = 'none'

# 导入大模型接口模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from large_models_interfaces.llm_single_turn_interface import QwenModelInterface

# 导入动作组字典
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'TonyPi'))
from ActionGroupDict import action_group_dict


class LLMProcessor:
    """大语言模型处理器，将自然语言指令转换为结构化的动作序列"""
    
    def __init__(self):
        """初始化大语言模型处理器"""
        try:
            # 屏蔽stderr以抑制可能的错误消息
            stderr_fd = os.dup(2)
            devnull = open(os.devnull, 'w')
            os.dup2(devnull.fileno(), 2)
            
            # 初始化通义千问大模型接口
            self.llm = QwenModelInterface(model="qwen-plus")
            
            # 恢复stderr
            os.dup2(stderr_fd, 2)
            devnull.close()
            
            # 创建动作映射（中文名称到动作ID的映射）
            self.action_name_to_id = {}
            for action_id, action_name in action_group_dict.items():
                # 获取注释中的中文名称（如果有的话）
                chinese_name = self._extract_chinese_name(action_id, action_name)
                if chinese_name:
                    self.action_name_to_id[chinese_name] = action_id
            
            print("大语言模型处理器初始化成功")
        except Exception as e:
            print(f"大语言模型处理器初始化失败: {e}")
            sys.exit(1)
    
    def _extract_chinese_name(self, action_id: str, action_name: str) -> str:
        """
        从动作组字典中提取中文名称
        
        Args:
            action_id: 动作ID
            action_name: 动作名称
            
        Returns:
            str: 中文名称
        """
        # 定义一些常见动作的中文名称
        common_names = {
            'stand': '立正',
            'go_forward': '前进',
            'back_fast': '后退',
            'left_move_fast': '左移',
            'right_move_fast': '右移',
            'push_ups': '俯卧撑',
            'sit_ups': '仰卧起坐',
            'turn_left': '左转',
            'turn_right': '右转',
            'wave': '挥手',
            'bow': '鞠躬',
            'squat': '下蹲',
            'chest': '庆祝',
            'left_shot_fast': '左脚踢',
            'right_shot_fast': '右脚踢',
            'wing_chun': '咏春',
            'left_uppercut': '左勾拳',
            'right_uppercut': '右勾拳',
            'left_kick': '左侧踢',
            'right_kick': '右侧踢',
            'stand_up_front': '前跌倒起立',
            'stand_up_back': '后跌倒起立',
            'twist': '扭腰',
            'stand_slow': '慢速立正',
            'stepping': '原地踏步',
            'jugong': '鞠躬',
            'weightlifting': '举重'
        }
        
        # 如果在常见动作中，返回对应中文名称
        if action_name in common_names:
            return common_names[action_name]
        
        # 否则返回动作名称本身
        return action_name
    
    def process_command(self, command_text: str) -> Dict:
        """
        处理自然语言指令，转换为结构化的动作序列
        
        Args:
            command_text: 自然语言指令
            
        Returns:
            Dict: 包含文本回复和动作序列的字典
        """
        if not command_text:
            print("命令文本为空")
            return {"text_response": "我没有听清您的指令", "action_sequence": []}
        
        print(f"处理指令: {command_text}")
        
        # 构建系统提示词
        system_prompt = self._build_prompt()
        
        try:
            # 屏蔽stderr以抑制可能的错误消息
            stderr_fd = os.dup(2)
            devnull = open(os.devnull, 'w')
            os.dup2(devnull.fileno(), 2)
            
            # 调用大模型获取回复
            llm_response = self.llm.get_response(
                user_prompt=f"用户指令: {command_text}",
                system_prompt=system_prompt
            )
            
            # 恢复stderr
            os.dup2(stderr_fd, 2)
            devnull.close()
            
            print(f"大模型原始回复: {llm_response}")
            
            # 解析JSON结果
            result = self._parse_llm_response(llm_response)
            
            # 验证结果
            if self._validate_result(result):
                return result
            else:
                return {"text_response": "我无法理解您的指令", "action_sequence": []}
            
        except Exception as e:
            print(f"调用大模型处理指令时出错: {e}")
            return {"text_response": "处理指令时出错，请重试", "action_sequence": []}
    
    def _build_prompt(self) -> str:
        """
        构建系统提示词
        
        Returns:
            str: 系统提示词
        """
        # 构建可用动作列表字符串
        action_list = []
        for action_id, action_name in action_group_dict.items():
            # 获取中文名称
            chinese_name = self._extract_chinese_name(action_id, action_name)
            action_list.append(f"- {chinese_name} (动作号: {action_id})")
        
        action_list_str = "\n".join(action_list)
        
        return f"""
        你是一个智能机器人助手。你的任务是将用户的自然语言指令，解析成一个标准化的动作序列。

        # 可用动作列表
        这是你能够执行的所有动作和它们对应的唯一"动作号"：
        {action_list_str}

        # 你的任务
        1. 理解用户指令中的动作顺序，指令中可能包含重复的动作。
        2. 生成一段确认性的文本回复，用友好的语气复述你将要执行的动作顺序。例如："好的，我将先...，再...，最后..."。如果只有一个动作，不用说“先”和“最后”，直接说出要做的动作即可。
        3. 创建一个JSON对象，其中包含这个文本回复和一个名为 "action_sequence" 的数组。
        4. 在 "action_sequence" 数组中，列出要执行的动作。每个动作都是一个包含 "sequence_id"（从1开始的执行序号）和 "action_id"（对应的动作号）的对象。

        # 输出格式要求
        请严格按照以下JSON格式返回，不要添加任何额外的解释或文字。
        {{
          "text_response": "好的，我将先执行A，再执行B。",
          "action_sequence": [
            {{
              "sequence_id": 1,
              "action_id": "动作号A"
            }},
            {{
              "sequence_id": 2,
              "action_id": "动作号B"
            }}
          ]
        }}
        注意，这里的action_id需要返回字符串形式的数字！！！
        """
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        从大模型回复中解析JSON结果
        
        Args:
            response_text: 大模型回复文本
            
        Returns:
            Dict: 解析后的结果
        """
        try:
            # 查找回复中的JSON内容
            json_start_index = response_text.find('{')
            json_end_index = response_text.rfind('}')
            
            if json_start_index != -1 and json_end_index != -1:
                # 提取JSON字符串
                json_str = response_text[json_start_index:json_end_index + 1]
                # 解析JSON
                result = json.loads(json_str)
                return result
            else:
                # 如果没有找到JSON格式的回复，创建一个错误响应
                print("未找到有效的JSON格式响应")
                return {"text_response": "我无法理解您的指令", "action_sequence": []}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"text_response": "处理指令时出错，请重试", "action_sequence": []}
    
    def _validate_result(self, result: Dict) -> bool:
        """
        验证解析结果是否有效
        
        Args:
            result: 解析结果
            
        Returns:
            bool: 是否有效
        """
        try:
            # 检查必要的字段是否存在
            if "text_response" not in result or "action_sequence" not in result:
                print("返回的JSON缺少必要字段")
                return False
            
            # 检查action_sequence是否为列表
            if not isinstance(result["action_sequence"], list):
                print("action_sequence 字段必须是一个列表")
                return False
            
            # 检查action_sequence中的每个项目是否有效
            for action in result["action_sequence"]:
                if "sequence_id" not in action or "action_id" not in action:
                    print("action_sequence 中的项目缺少必要字段")
                    return False
                
                # 检查action_id是否有效
                if action["action_id"] not in action_group_dict:
                    print(f"无效的 action_id: {action['action_id']}")
                    return False
            
            return True
        except Exception as e:
            print(f"验证结果时出错: {e}")
            return False


# 测试代码
if __name__ == "__main__":
    # 屏蔽ALSA错误消息
    os.environ['ALSA_CARD'] = 'none'
    
    processor = LLMProcessor()
    result = processor.process_command("请先原地踏步，然后做一个左勾拳，最后鞠个躬")
    print(json.dumps(result, ensure_ascii=False, indent=2)) 