"""
文本转语音接口 V2.0
核心功能是将文本转换为语音。主要用于将大模型返回的结果转换为语音后由机器人播报。
"""

# coding=utf-8
#
# pyaudio安装说明：
# 如果是macOS操作系统，执行如下命令：
#   brew install portaudio
#   pip install pyaudio
# 如果是Debian/Ubuntu操作系统，执行如下命令：
#   sudo apt-get install python-pyaudio python3-pyaudio
# 如果是CentOS操作系统，执行如下命令：
#   sudo yum install -y portaudio portaudio-devel && pip install pyaudio
# 如果Windows操作系统，执行如下命令：
#   python -m pip install pyaudio

from abc import ABC, abstractmethod
import time
import pyaudio
import dashscope
from dashscope.api_entities.dashscope_response import SpeechSynthesisResponse
from dashscope.audio.tts_v2 import *
import os
from datetime import datetime
import re
import sys
import ctypes

# 若没有将API Key配置到环境变量中，需将your-api-key替换为自己的API Key
api_key = os.environ.get("ALI_APIKEY")

if not api_key:
    raise ValueError("请在环境变量中配置ALI_APIKEY")

# 设置API Key
dashscope.api_key = api_key

class CosyVoiceInterface(ABC):
    @abstractmethod
    def text2speech(self, text) -> None:
        """
        文本转音频并直接输出音频
        Args:
            text: 待合成语音的文本
        """
        pass


# 定义回调接口
class Callback(ResultCallback):
    _player = None
    _stream = None
    _stderr_fd = None
    _original_stderr_fd = None

    def suppress_alsa_errors(self):
        # 保存原始stderr
        self._original_stderr_fd = os.dup(sys.stderr.fileno())
        self._stderr_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(self._stderr_fd, sys.stderr.fileno())

    def restore_stderr(self):
        if self._stderr_fd is not None and self._original_stderr_fd is not None:
            os.dup2(self._original_stderr_fd, sys.stderr.fileno())
            os.close(self._stderr_fd)

    def get_timestamp(self):
        now = datetime.now()
        return now.strftime("[%Y-%m-%d %H:%M:%S.%f]")

    def on_open(self):
        print("连接建立：" + self.get_timestamp())
        self.suppress_alsa_errors()  # <-- 屏蔽底层 stderr 输出
        self._player = pyaudio.PyAudio()
        self._stream = self._player.open(
            format=pyaudio.paInt16, channels=1, rate=22050, output=True
        )
        self.restore_stderr()  # <-- 语音设备初始化后恢复 stderr 输出

    def on_complete(self):
        print("语音合成完成，所有合成结果已被接收：" + self.get_timestamp())

    def on_error(self, message: str):
        print(f"语音合成出现异常：{message}")

    def on_close(self):
        print("连接关闭：" + self.get_timestamp())
        self._stream.stop_stream()
        self._stream.close()
        self._player.terminate()

    def on_event(self, message):
        pass

    def on_data(self, data: bytes) -> None:
        self._stream.write(data)

class CosyVoiceModel(CosyVoiceInterface):
    def __init__(self, model: str="cosyvoice-v2", voice: str="longshu_v2"):
        self.callback = Callback()
        '''
        model: 语音合成模型，默认为cosyvoice-v2
        voice: 语音合成音色，默认为longshu_v2
        '''
        self.model = model
        self.voice = voice
    
    # 文本分段
    def segment(self, text) -> list[str]:
        """按标点符号分段文本"""
        
        # 去除换行符（替换为空格）
        text = text.replace('\n', ' ')
        # 使用正则表达式按标点符号分段，同时保留标点符号
        pattern = r'([，。！？；：,.!?;:])'
        segments = re.split(pattern, text)
        
        # 过滤空字符串
        segments = [s for s in segments if s != '']
        
        # 合并标点符号到前一段落
        result = []
        for i in range(0, len(segments), 2):
            if i + 1 < len(segments):
                # 合并非标点段 + 标点段
                result.append(segments[i] + segments[i+1])
            else:
                # 处理最后一段无标点的情况
                result.append(segments[i])
        return result

    def text2speech(self, text) -> None:
        # 文本分段
        textList = self.segment(text)

        # 实例化SpeechSynthesizer，并在构造方法中传入模型（model）、音色（voice）等请求参数
        synthesizer = SpeechSynthesizer(
            model=self.model,
            voice=self.voice,
            format=AudioFormat.PCM_22050HZ_MONO_16BIT,  
            callback=self.callback,
        )

        # 流式发送待合成文本。在回调接口的on_data方法中实时获取二进制音频
        for text in textList:
            synthesizer.streaming_call(text)
            time.sleep(0.1)
            
        # 结束流式语音合成
        synthesizer.streaming_complete()


if __name__ == '__main__':
    text = '你好，欢迎使用语音合成服务。今天的天气真不错，今天的天气真不错，今天的天气真不错。'
    CosyVModel = CosyVoiceModel()

    CosyVModel.text2speech(text)