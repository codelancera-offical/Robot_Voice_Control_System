"""
ASR语音识别类，基于Vosk和PyAudio。
支持多热词拼音流式检测，每个热词有独立指针，实时检测拼音序列，匹配即返回信号。
"""
import sys
import os
from vosk import Model, KaldiRecognizer
import pyaudio
import json
from pypinyin import lazy_pinyin
import threading
import numpy as np

# 获取当前脚本所在文件夹的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取上级目录路径
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)

from large_models_interfaces.get_device_and_rate import get_input_device

class HotwordSequence:
    def __init__(self, name, pinyin_seq, signal):
        self.name = name
        self.pinyin_seq = pinyin_seq  # 期望的拼音序列
        self.signal = signal          # 匹配到后返回的信号
        self.pointer = 0             # 当前匹配到第几个拼音

    def reset(self):
        self.pointer = 0

    def match(self, pinyin_stream):
        """
        在拼音流中推进指针，若完全匹配则返回True，否则False。
        匹配失败时指针回到0。
        """
        # 思路说明：
        # 1. 遍历输入的拼音流，每次取一个拼音p。
        # 2. 如果p是空格，直接跳过（因为拼音流中可能有空格分隔）。
        # 3. 如果p等于当前热词序列指针所指的拼音（self.pinyin_seq[self.pointer]），指针前进一位。
        #    - 如果指针已经到达热词序列末尾，说明完全匹配，重置指针并返回True。
        # 4. 如果p不等于当前指针所指拼音，说明匹配失败，指针重置为0。
        #    - 但如果p正好等于热词序列的第一个拼音，指针设为1（支持“重叠”匹配）。
        # 5. 如果遍历结束都没有完全匹配，返回False。
        for p in pinyin_stream:
            if p == ' ':
                continue
            elif p == self.pinyin_seq[self.pointer]:
                self.pointer += 1
                if self.pointer == len(self.pinyin_seq):
                    self.reset()
                    return True
            else:
                self.reset()
                if p == self.pinyin_seq[0]:
                    self.pointer = 1
        return False

class AsrVosk:
    def __init__(self, model_path, hotwords_dict, sample_rate=16000):
        """
        model_path: 语音识别模型路径
        hotwords_dict: {热词: 信号值} 的字典
        sample_rate: 采样率，默认16000
        """
        self.model = Model(model_path)
        self.device_index, self.sample_rate = get_input_device(sample_rate=sample_rate)
        self.rec = KaldiRecognizer(self.model, self.sample_rate)
        
        self.stream = None
        # 构建热词序列对象列表
        self.hotword_sequences = []
        for word, signal in hotwords_dict.items():
            pinyin_seq = lazy_pinyin(word)
            self.hotword_sequences.append(HotwordSequence(word, pinyin_seq, signal))

    def start(self):
        self.p = pyaudio.PyAudio()
        
        # 先获取设备信息
        print("=== 设备扫描 ===")
        input_devices = []
        for i in range(self.p.get_device_count()):
            try:
                dev_info = self.p.get_device_info_by_index(i)
                if int(dev_info['maxInputChannels']) > 0:
                    print(f"设备 {i}: {dev_info['name']}")
                    print(f"  默认采样率: {dev_info['defaultSampleRate']} Hz")
                    print(f"  输入通道: {dev_info['maxInputChannels']}")
                    print(f"  主机API: {dev_info['hostApi']}")
                    input_devices.append((i, dev_info))
            except Exception as e:
                print(f"设备 {i} 信息获取失败: {e}")
        print("=" * 30)
        
        # 保存设备列表供后续使用
        self.input_devices = input_devices
        
        # 打开音频流（不指定设备，让PyAudio自动选择）
        print("正在打开音频流（自动选择设备）...")
        # self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True, frames_per_buffer=4096)
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024,  # 修复：添加缓冲区大小
            input_device_index=self.device_index
        )
        # 你的程序 → PyAudio → ALSA → USB麦克风 这条路走的通
        self.stream.start_stream()
  

    def stop(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

    def cleanup(self):
        """清理所有资源"""
        try:
            if hasattr(self, 'stream') and self.stream is not None:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None
            if hasattr(self, 'p') and self.p is not None:
                try:
                    self.p.terminate()
                except Exception:
                    pass
                self.p = None
        except Exception as e:
            print(f"清理资源时发生错误: {e}")

    def __del__(self):
        """析构函数，确保资源被释放"""
        self.cleanup()
        
    def resample_audio(self, data: bytes) -> bytes:
        """将音频数据重采样到16kHz"""
        # 将字节数据转换为numpy数组
        audio_array = np.frombuffer(data, dtype=np.int16)
        
        # 重采样
        resampled = librosa.resample(
            audio_array.astype(np.float32),
            orig_sr=self.actual_sample_rate,
            target_sr=self.target_sample_rate
        )
        
        # 转换回int16并打包为字节
        resampled = resampled.astype(np.int16).tobytes()
        return resampled

    def listen_for_hotword(self):
        """
        阻塞式监听，实时检测拼音流，匹配到热词序列即返回信号。
        """
        self.start()
        try:
            while self.stream is not None:
                try:
                    # 读取音频数据，设置exception_on_overflow=False避免溢出错误
                    data = self.stream.read(1024, exception_on_overflow=False)
                    
                    # 重采样：从48kHz到16kHz (每3个样本取1个)
                    
                    data = self.resample_audio(data)
                    
                    # 发送给Vosk识别
                    self.rec.AcceptWaveform(resampled_data)
                    
                    result = self.rec.PartialResult()
                    try:
                        text = json.loads(result).get('partial', '')
                        print(f"中间结果：{text}")
                    except Exception:
                        text = ''
                    pinyin_stream = lazy_pinyin(text)
                    print(f"拼音流：{pinyin_stream}")
                    # 多热词并发检测
                    for seq in self.hotword_sequences:
                        if seq.match(pinyin_stream):
                            # 清空PartialResult
                            self.rec.Reset()
                            return seq.signal
                except Exception as e:
                    print(f"处理音频数据时出错: {e}")
                    break
        except KeyboardInterrupt:
            print("用户中断了监听")
            return None
        except Exception as e:
            print(f"监听过程中发生错误: {e}")
            return None
        finally:
            self.stop()

if __name__ == "__main__":
    # 示例用法：检测到"小心 小心"或"再见"时返回对应信号
    hotwords = {"小新小新": 1, "再见": 2}
    asr = AsrVosk("./vosk-model-small-cn-0.22", hotwords)
    print("请说话，等待检测热词……")
    
    try:
        signal = asr.listen_for_hotword()
        if signal is not None:
            print(f"检测到热词，返回信号：{signal}")
        else:
            print("未检测到热词或发生错误")
    except KeyboardInterrupt:
        print("程序被用户中断")
    finally:
        # 确保资源被释放
        asr.cleanup() 