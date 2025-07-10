"""
图像描述接口 V2.0
核心功能是分析图像并生成描述，主要用于将图像交给视觉大模型进行分析并得到分析结果。
"""

import os
import base64
from abc import ABC, abstractmethod
from openai import OpenAI
from typing import Optional

# -------------------- 步骤 1: 定义图片描述服务的接口 (抽象基类) --------------------
class ImageDescriptionInterface(ABC):
    """
    定义一个图像描述服务的标准接口。
    所有具体的视觉模型实现都应该继承这个类。
    """

    @abstractmethod
    def describe_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        """
        接收一个本地图片路径，返回模型对图片的文字描述。

        Args:
            image_path (str): 本地图像文件的绝对或相对路径。
            prompt (str, optional): 自定义提问。如果为 None，则使用默认提问。

        Returns:
            str: 模型生成的对图片的描述文本。
        """
        pass


# -------------------- 步骤 2: 实现接口，封装通义千问视觉语言模型 --------------------
class QwenVLModelInterface(ImageDescriptionInterface):
    """
    通义千问视觉语言（Qwen-VL）模型的具体实现，遵循 ImageDescriptionInterface 接口。
    """

    def __init__(self, model: str = "qwen-vl-max"):
        """
        初始化通义千问视觉语言模型客户端。

        Args:
            model (str): 要使用的具体模型名称，例如 "qwen-vl-max", "qwen-vl-plus" 等。
        """
        self.model_name = model
        try:
            # 优先从环境变量 DASHSCOPE_API_KEY 中获取 API Key
            api_key = os.getenv("ALI_APIKEY")
            if not api_key:
                raise ValueError("环境变量 'DASHSCOPE_API_KEY' 未设置，请先设置。")
            
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        except Exception as e:
            print(f"初始化OpenAI客户端失败: {e}")
            raise

    def _encode_image_and_get_mime_type(self, image_path: str) -> (str, str):
        """
        一个私有辅助方法，用于将图片编码为Base64并自动识别MIME类型。
        """
        # 从文件扩展名推断MIME类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
        
        if ext not in mime_map:
            raise ValueError(f"不支持的图片格式: {ext}。仅支持 .png, .jpg, .jpeg, .webp")
        
        mime_type = mime_map[ext]

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        
        return encoded_string, mime_type

    def describe_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        """
        实现接口定义的 describe_image 方法。
        """
        if not os.path.exists(image_path):
            return f"错误：找不到图片文件 '{image_path}'"
            
        try:
            base64_image, mime_type = self._encode_image_and_get_mime_type(image_path)
        except (ValueError, FileNotFoundError) as e:
            return f"处理图片时出错: {e}"

        # 如果用户未提供自定义prompt，则使用默认值
        final_prompt = prompt if prompt else "图中描绘的是什么景象?"

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "你是一个视觉AI助手，负责根据用户要求返回图片描述，注意，你应该生成纯文本段来描述，不要使用任何特殊符号或者emoji！"}]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    },
                    {"type": "text", "text": final_prompt},
                ],
            }
        ]

        try:
            print(f"正在向 {self.model_name} 模型发送图片和请求...")
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            response_content = completion.choices[0].message.content
            return response_content.strip() if response_content else "未能获取有效的描述。"
        except Exception as e:
            error_message = f"调用视觉API时出错: {e}"
            print(error_message)
            return error_message


# -------------------- 步骤 3: 在主程序块中测试接口实现 --------------------
if __name__ == "__main__":
    print("--- 开始测试通义千问视觉模型接口 ---")
    
    # ！！！重要！！！
    # 请将下面的路径替换为您自己本地图片的真实路径
    # 例如: "C:/Users/YourUser/Pictures/my_cat.jpg" 或 "/home/user/images/eagle.png"
    IMAGE_PATH = "REPLACE_WITH_YOUR_IMAGE_PATH.png"

    if IMAGE_PATH == "REPLACE_WITH_YOUR_IMAGE_PATH.png":
        print("\n错误：请先在代码中设置 IMAGE_PATH 变量为您本地图片的路径！")
    else:
        try:
            # 1. 创建 QwenVLModel 实例
            vision_model = QwenVLModelInterface(model="qwen-vl-max")

            # --- 测试1: 使用默认提问 ---
            print("\n--- 测试1: 使用默认提问 ---")
            description = vision_model.describe_image(IMAGE_PATH)
            print(f"\n[图片路径]: {IMAGE_PATH}")
            print(f"[模型描述]: {description}")

            # --- 测试2: 使用自定义提问 ---
            print("\n\n--- 测试2: 使用自定义提问 ---")
            custom_prompt = "这张图片里有多少只动物？它们分别是什么？"
            custom_description = vision_model.describe_image(IMAGE_PATH, prompt=custom_prompt)
            print(f"\n[自定义问题]: {custom_prompt}")
            print(f"[模型回答]: {custom_description}")

        except Exception as e:
            print(f"\n测试过程中发生严重错误: {e}")
            print("请确保你已正确安装 'openai' 库 (pip install openai)")
