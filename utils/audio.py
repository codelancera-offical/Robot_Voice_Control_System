"""
音频工具 V2.0
音频工具模块提供了音频播放和生成的基本功能，是系统语音交互的基础设施。
"""

import wave
import pyaudio
import os
import sys
import dashscope
from dashscope.audio.tts_v2 import *
from pydub import AudioSegment
import io


def play_wav(filename: str):
    """
    使用 PyAudio 播放指定的 WAV 文件。
    Args:
        filename (str): 要播放的 WAV 文件路径。
    """
    if not os.path.exists(filename):
        print(f"错误: WAV 文件 '{filename}' 不存在。")
        return

    try:
        wf = wave.open(filename, 'rb')
    except wave.Error as e:
        print(f"错误: 无法打开 WAV 文件 '{filename}' - {e}")
        return

    # 初始化 PyAudio
    p = pyaudio.PyAudio()

    # 打开音频流
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # 读取数据并播放
    chunk = 1024 # 每次读取的帧数
    data = wf.readframes(chunk)
    print(f"[play_wav] 正在播放文件: {filename}")
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    # 停止并关闭流
    stream.stop_stream()
    stream.close()

    # 终止 PyAudio
    p.terminate()
    wf.close()
    print(f"[play_wav] 文件 '{filename}' 播放完毕。")

def generate_wav(
    text: str,
    output_wav_path: str,
    model: str = "cosyvoice-v2",
    voice: str = "longshu_v2",
    api_key: str = None
) -> bool:
    """
    将指定文本合成为语音，并将其保存为WAV格式的音频文件。

    Args:
        text (str): 待合成的文本内容。
        output_wav_path (str): 输出WAV文件的完整路径（例如："path/to/output.wav"）。
        model (str, optional): 用于语音合成的模型名称。默认为 "cosyvoice-v2"。
        voice (str, optional): 用于语音合成的音色名称。默认为 "longshu_v2"。
        api_key (str, optional): DashScope API Key。如果未提供，将尝试从环境变量 "ALI_APIKEY" 中获取。

    Returns:
        bool: 如果语音合成、转换和文件写入成功，则返回 True；否则返回 False。
    """
    # 设置DashScope API Key
    if api_key:
        dashscope.api_key = api_key
    elif os.getenv("ALI_APIKEY"):
        dashscope.api_key = os.getenv("ALI_APIKEY")
    else:
        print("错误: DashScope API Key未设置。请通过参数传入或设置环境变量 'ALI_APIKEY'。")
        return False

    # 确保输出目录存在
    output_dir = os.path.dirname(output_wav_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        except OSError as e:
            print(f"错误: 无法创建目录 {output_dir}: {e}")
            return False

    print(f"开始合成文本: '{text}' 到文件: '{output_wav_path}'")

    try:
        # 实例化SpeechSynthesizer
        synthesizer = SpeechSynthesizer(model=model, voice=voice)

        # 发送待合成文本，获取二进制音频（默认为MP3格式）
        audio_mp3_bytes = synthesizer.call(text)

        print('[Metric] requestId为：{}，首包延迟为：{}毫秒'.format(
            synthesizer.get_last_request_id(),
            synthesizer.get_first_package_delay()))

        # 将MP3字节数据加载为pydub的AudioSegment对象
        mp3_audio_stream = io.BytesIO(audio_mp3_bytes)
        audio_segment = AudioSegment.from_file(mp3_audio_stream, format="mp3")

        # 将AudioSegment对象导出为WAV文件
        audio_segment.export(output_wav_path, format="wav")

        print(f"语音已成功合成并转换为WAV格式，保存到: {output_wav_path}")
        return True

    except Exception as e:
        print(f"处理音频时发生错误: {e}")
        print("请确保您已安装 pydub 库，并且 ffmpeg 已正确安装并配置到系统PATH中。")
        return False
