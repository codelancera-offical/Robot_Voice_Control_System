"""
语音转文本接口 V2.0
核心功能是将语音转换为文本，主要用于将用户说的自然语言转换为文本后交给大模型处理。
"""

# For prerequisites running the following sample, visit https://help.aliyun.com/document_detail/611472.html
import sys
import os
import time
from dashscope.audio.asr import *
import dashscope
import pyaudio
import numpy as np
from abc import ABC, abstractmethod
from datetime import datetime

# 获取当前脚本所在文件夹的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上级目录路径
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)
from utils.keyboard_monitor import KeyboardMonitor  # 导入键盘监控类
from get_device_and_rate import get_input_device  # 导入获取输入设备和采样率函数


# 新增导入
import librosa
import io


# 屏蔽ALSA错误消息
os.environ['ALSA_CARD'] = 'none'

# 若没有将API Key配置到环境变量中，需将your-api-key替换为自己的API Key
api_key = os.environ.get("ALI_APIKEY")

if not api_key:
    raise ValueError("请在环境变量中配置ALI_APIKEY")

# 设置API Key
dashscope.api_key = api_key


CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1

mindb = 3000 # 声音阈值，用于判断是否开始或停止计时

model = "paraformer-realtime-v2"  # 模型名称
sample_rate = 16000  # 音频采样率

def get_delayTime(CHUNK, sample_rate):
    end_time = 2.4  # 小声2.4秒后自动终止 公式：CHUNK * delayTime / RATE = 2.4s
    delayTime = int(end_time * sample_rate / CHUNK)
    return delayTime

class ParaformerInterface(ABC):
    
    @abstractmethod
    def speech2text(self) -> str:
        '''
        语音转文本接口
        return: 
            str: 语音转文本结果
        '''
        pass


class Callback(RecognitionCallback):
    def __init__(self, sample_rate: int, input_device_index: int):
        super().__init__()
        self.text = ""  # 用于存储完整的识别文本
        self.sample_rate = sample_rate

        self.target_sample_rate = 16000  # 目标采样率
        self.actual_sample_rate = sample_rate  # 设备实际采样率
        self.device_index = input_device_index
        self.need_resample = (self.actual_sample_rate != self.target_sample_rate)

    
        
    def get_timestamp(self):
        now = datetime.now()
        formatted_timestamp = now.strftime("[%Y-%m-%d %H:%M:%S.%f]")
        return formatted_timestamp

    def on_open(self) -> None:
        global stream
        global p
        p = pyaudio.PyAudio()
        input_device_index = 0
        stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=CHUNK,
			        input_device_index=self.device_index)
    
    def on_close(self) -> None:
        global stream
        global p
        stream.stop_stream()
        stream.close()
        p.terminate()
        stream = None
        p = None

    def on_complete(self) -> None:
        print(self.get_timestamp() + ' Recognition completed 语音识别结束')  # recognition complete

    def on_error(self, result: RecognitionResult) -> None:
        print('Recognition task_id: ', result.request_id)
        print('Recognition error: ', result.message)
        if 'stream' in globals() and stream.active:
            stream.stop_stream()
            stream.close()
        exit(0)

    def on_event(self, result: RecognitionResult) -> None:
        
        sentence = result.get_sentence()
        if 'text' in sentence:
            # print(self.get_timestamp() + ' RecognitionCallback text: ', sentence['text'])
            if RecognitionResult.is_sentence_end(sentence):
                self.text = sentence['text']
                # print(self.get_timestamp() + 
                #     'RecognitionCallback sentence end, request_id:%s, usage:%s'
                #     % (result.get_request_id(), result.get_usage(sentence)))

class ParaformerModel(ParaformerInterface):
    def __init__(self,model: str="paraformer-realtime-v2",sample_rate: int=16000,format: str='wav'):
        """
        初始化模型
        Args:
            model (str, optional): 模型名称. Defaults to "paraformer-realtime-v2".
            sample_rate (int, optional): 音频采样率. Defaults to 16000.
            format (str, optional): 音频格式. Defaults to 'wav'.
        """
        self.target_device_name = "USB PnP Audio Device"  # 指定目标设备名称
        self.device_index, self.sample_rate = get_input_device(sample_rate, self.target_device_name)

        self.callback = Callback(self.sample_rate, self.device_index)
        self.model = model
        self.format = format
        self.keyboard_monitor = KeyboardMonitor()  # 创建键盘监控实例
        self.delayTime = get_delayTime(CHUNK, self.sample_rate)  # 获取延迟时间
        self.recognition = Recognition(model=model,
                            format=format,
                            sample_rate=16000,
                            # "language_hints"只支持paraformer-realtime-v2模型
                            language_hints=['zh', 'en'],
                            callback=self.callback)

    def resample_audio(self, data: bytes) -> bytes:
        """将音频数据重采样到16kHz"""
        # 将字节数据转换为numpy数组
        audio_array = np.frombuffer(data, dtype=np.int16)
        
        # 重采样
        resampled = librosa.resample(
            audio_array.astype(np.float32),
            orig_sr=self.callback.actual_sample_rate,
            target_sr=self.callback.target_sample_rate
        )
        
        # 转换回int16并打包为字节
        resampled = resampled.astype(np.int16).tobytes()
        return resampled
        
    def record(self) -> None:
        """
        录音函数
        运行后会进行录音，声音过小到一定时间后会自动停止
        按下回车键可以立即结束录音
        """
        try:
            frames = []
            start = True # 是否继续录音
            start2 = False # 是否开始进行停止计时

            tempnum = 0  # tempnum、tempnum2为计时量
            tempnum2 = 0

            print("开始录音 (按回车键结束)")
            while start:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                audio_data = np.frombuffer(data, dtype=np.short)
                temp = np.max(audio_data)

                # 如果需要重采样
                if self.callback.need_resample:
                    data = self.resample_audio(data)

                if (temp < mindb and start2 == False): # 小声检测
                    start2 = True
                    tempnum2 = tempnum

                if (temp > mindb):
                    start2 = False
                    tempnum2 = tempnum

                if (tempnum > tempnum2 + self.delayTime and start2 == True): # 停止录音判断
                    if (start2 and temp < mindb):
                        start = False
                    else:
                        start2 = False
                
                # 检测是否按下回车键
                if self.keyboard_monitor.is_enter_pressed():
                    print("\n检测到回车键，立即结束录音")
                    start = False
                
                # 添加实时音量可视化
                vol_bar = "|" * min(20, int(temp / 500))  # 简易音量条
                print(f"\r倒计时: {max(0, (tempnum2 + self.delayTime - tempnum)*CHUNK/self.sample_rate):.1f}s 音量: [{vol_bar:<20}]", end="")
                
                # 发送音频数据到服务端
                self.recognition.send_audio_frame(data)

                tempnum += 1

            print("\n录音结束")
                
        except Exception as e:
            raise e


    def speech2text(self) -> str:
        self.callback.text = ""
        
        try:
            self.recognition.start()
            self.record()
            self.recognition.stop()
        finally:
            # 确保恢复终端设置
            self.keyboard_monitor.restore_terminal()

        return self.callback.text

if __name__ == '__main__':
    model = ParaformerModel(model=model,sample_rate=sample_rate)
    text = model.speech2text()
    print(text)
