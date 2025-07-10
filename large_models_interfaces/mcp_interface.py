"""
MCP接口 V2.0
核心功能是提供MCP接口，主要用于实现机器人和MCP应用智能体之间的交互。
"""

import os
from http import HTTPStatus
from dashscope import Application
from abc import ABC, abstractmethod

class MCPInterface(ABC):
    @abstractmethod
    def get_response(self, text) -> str:
        pass

class MCPModel(MCPInterface):
    def __init__(self, app_id: str='', system_prompt: str='', memory: bool = True):
        '''
        app_id: (必选)阿里云MCP应用ID
        system_prompt: 系统提示语
        memory: 是否进行上下文多轮对话
        '''
        self.API_KEY = os.environ.get("ALI_APIKEY")
        if self.API_KEY is None:
            raise ValueError('请在环境变量中设置ALI_APIKEY')
        
        self.APP_ID = app_id if app_id != '' else os.environ.get("ALI_APPID")
        if self.APP_ID == '' or self.APP_ID is None:
            raise ValueError('请设置阿里云MCP应用ID')
        
        self.memory = memory
        self.message = []
        self.system_prompt=system_prompt
        
        # 设置系统提示词
        if system_prompt != '':
            self.message.append({"role": "system", "content": system_prompt})
        else:
            self.message.append({"role": "system", "content": "你是一个智能家居机器人，输出要口语化，纯文本，不要生成markdown格式的文本，不要有任何特殊符号，但可以有标点符号，不要有什么分段的格式，不要有链接、图片。"})

    # 重置消息
    def reset_message(self) -> None:
        if self.system_prompt != '':
                self.message = [{"role": "system", "content": self.system_prompt}]
        else:
                self.message = []
    
    # 获取大模型回复
    def get_response(self, text) -> str:
        '''
        text: 用户输入的文本
        '''
        # 不进行上下文多轮对话
        if not self.memory:
            self.reset_message()
        
        self.message.append({"role": "user", "content": text})
        
        print("正在调用大模型")
        # 调用阿里云MCP接口
        response = Application.call(app_id=self.APP_ID, api_key=self.API_KEY, messages=self.message)
        print("调用大模型结束")
        
        if response.status_code == HTTPStatus.OK:
            #print(response.output.text)
            # 保存上下文多轮对话
            self.message.append({"role": "assistant", "content": response.output.text})
            return response.output.text
        else:
            print(f'request_id={response.request_id}')
            print(f'code={response.status_code}')
            print(f'message={response.message}')
            print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
            print("重置大模型对话信息")
            self.reset_message()
            return "调用大模型失败"
        
if __name__ == '__main__':
    mcp_model = MCPModel(app_id='', system_prompt='', memory=True)
    response_text = mcp_model.get_response('我想知道武汉今天的天气')
    print(response_text)