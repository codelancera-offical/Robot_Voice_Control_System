# coding=utf-8

"""
语音生成工具 V2.0
本工具可独立于主程序运行，可调用API来将指定文本生成为高质量的WAV格式语音文件。
"""

import dashscope
from dashscope.audio.tts_v2 import *
import os
from pydub import AudioSegment # 导入 pydub 库
import io # 导入 io 模块，用于处理字节流

# 若没有将API Key配置到环境变量中，需将your-api-key替换为自己的API Key
dashscope.api_key = os.getenv("ALI_APIKEY")

# 模型
model = "cosyvoice-v2"
# 音色
voice = "longshu_v2"

# 实例化SpeechSynthesizer，并在构造方法中传入模型（model）、音色（voice）等请求参数
synthesizer = SpeechSynthesizer(model=model, voice=voice)

# 获取用户输入
#text_to_synthesize = input("请输入要生成语音的文段：")
text_to_synthesize = "拍照失败"
# 发送待合成文本，获取二进制音频（默认为MP3格式）
audio_mp3_bytes = synthesizer.call(text_to_synthesize)

print('[Metric] requestId为：{}，首包延迟为：{}毫秒'.format(
    synthesizer.get_last_request_id(),
    synthesizer.get_first_package_delay()))

# --- 新增的MP3到WAV转换和写入步骤 ---

# 1. 将MP3字节数据加载为pydub的AudioSegment对象
# 使用io.BytesIO将字节数据包装成文件对象，以便pydub可以读取
mp3_audio_stream = io.BytesIO(audio_mp3_bytes)
try:
    audio_segment = AudioSegment.from_file(mp3_audio_stream, format="mp3")

    # 2. 定义WAV文件的输出路径
    #output_wav_path = input("请输入输出文件路径：")
    output_wav_path = 'paizao.wav'
    
    # 3. 将AudioSegment对象导出为WAV文件
    audio_segment.export(output_wav_path, format="wav")

    print(f"语音已成功合成并转换为WAV格式，保存到: {output_wav_path}")

except Exception as e:
    print(f"处理音频时发生错误: {e}")
    print("请确保您已安装 pydub 库，并且 ffmpeg 已正确安装并配置到系统PATH中。")

