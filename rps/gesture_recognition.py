#!/usr/bin/python3
# coding=utf8

"""
猜拳游戏 手势识别模块 V2.0
"""

import os
import traceback
from dashscope import MultiModalConversation

class GestureRecognition:
    """手势识别器：负责识别用户手势"""
    
    def __init__(self):
        """初始化手势识别器"""
        self.api_key = os.environ.get('ALI_APIKEY', '')
        self.model = 'qwen-vl-max-latest'
        self.options = ["石头", "剪刀", "布"]
        
    def recognize_from_image(self, image_path):
        """从图像中识别手势
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            str: 识别结果，包括"石头"、"剪刀"、"布"或"无结果"
        """
        if not os.path.exists(image_path):
            print(f"手势识别：图像文件不存在: {image_path}")
            return "无结果"
            
        image_uri = f'file://{image_path}'
        messages = [
            {"role": "system", "content": [{"text": "你是一个猜拳游戏的裁判。你需要识别图片中的手势是石头、剪刀还是布。只返回'石头'、'剪刀'、'布'或'无结果'之一，不要返回其他内容。"}]},
            {"role": "user", "content": [{"image": image_uri}, {"text": "这个手势是什么？只回答'石头'、'剪刀'、'布'或'无结果'之一，不要回答其它任何内容。"}]}
        ]
        
        try:
            print("手势识别：正在调用大模型识别手势...")
            
            # 添加超时设置和重试机制
            import time
            max_retries = 3
            timeout_seconds = 30
            
            for attempt in range(max_retries):
                try:
                    print(f"手势识别：第 {attempt + 1} 次尝试调用API...")
                    
                    # 设置请求超时
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError("API调用超时")
                    
                    # 设置30秒超时
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(timeout_seconds)
                    
                    try:
                        response = MultiModalConversation.call(
                            api_key=self.api_key,
                            model=self.model,
                            messages=messages
                        )
                        
                        # 取消超时
                        signal.alarm(0)
                        
                        print(f"手势识别：API调用成功，响应: {response}")
                        return self._parse_api_response(response)
                        
                    except TimeoutError:
                        print(f"手势识别：第 {attempt + 1} 次尝试超时")
                        signal.alarm(0)  # 取消超时
                        if attempt < max_retries - 1:
                            print("手势识别：等待5秒后重试...")
                            time.sleep(5)
                        else:
                            print("手势识别：所有重试都失败了")
                            return "无结果"
                            
                except Exception as e:
                    print(f"手势识别：第 {attempt + 1} 次尝试失败: {e}")
                    if attempt < max_retries - 1:
                        print("手势识别：等待3秒后重试...")
                        time.sleep(3)
                    else:
                        print("手势识别：所有重试都失败了")
                        return "无结果"
                        
        except Exception as e:
            print("手势识别：识别API调用失败:", e)
            traceback.print_exc()
            return "无结果"
    
    def _parse_api_response(self, response):
        """解析API返回的响应
        
        Args:
            response: API返回的原始响应
            
        Returns:
            str: 解析后的手势结果
        """
        if (response and "output" in response and 
            "choices" in response["output"] and 
            len(response["output"]["choices"]) > 0 and
            "message" in response["output"]["choices"][0]):
            
            message = response["output"]["choices"][0]["message"]
            if hasattr(message, "content") and len(message.content) > 0:
                if "text" in message.content[0]:
                    text = message.content[0]["text"].strip()
                    
                    # 确保结果是四个选项之一
                    if "石头" in text:
                        return "石头"
                    elif "剪刀" in text:
                        return "剪刀"
                    elif "布" in text:
                        return "布"
        
        print("手势识别：API返回格式异常或无法识别")
        return "无结果" 