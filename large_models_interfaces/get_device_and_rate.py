"""
获取音频设备接口 V2.0
核心功能是获取设备信息和音频采样率，主要用于扫描系统中所有可用的音频输入设备。
"""

import pyaudio

FORMAT = pyaudio.paInt16  # 音频数据格式

# 获取设备信息和音频采样率
def get_input_device(sample_rate: int, device_name: str="USB PnP Audio Device"):
        """查找特定USB音频设备并检查支持的采样率"""
        target_device_index = None
        target_rate = sample_rate
        target_device_name = device_name
        
        p = pyaudio.PyAudio()

        print("搜索音频设备...")
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                device_name = dev_info['name']
                print(f"设备 {i}: {device_name}")
                
                # 检查是否为目标USB设备
                if target_device_name in device_name:
                    print(f"  → 找到目标设备: {target_device_name}")
                    target_device_index = i
                    
                    # 检查支持的采样率
                    try:
                        # 优先尝试16000Hz
                        if p.is_format_supported(
                            target_rate,
                            input_device=i,
                            input_channels=1,
                            input_format=FORMAT
                        ):
                            print(f"  ✓ 支持 {target_rate}Hz 采样率")
                            break
                        
                        # 尝试设备默认采样率
                        default_rate = int(dev_info['defaultSampleRate'])
                        print(f"  ! 不支持 {target_rate}Hz, 尝试默认采样率: {default_rate}Hz")
                        sample_rate = default_rate
                        break
                    except Exception as e:
                        print(f"  采样率检查错误: {str(e)}")
                        # 尝试通用采样率
                        common_rates = [44100, 48000, 22050, 16000, 8000]
                        for rate in common_rates:
                            try:
                                if p.is_format_supported(
                                    rate,
                                    input_device=i,
                                    input_channels=1,
                                    input_format=FORMAT
                                ):
                                    print(f"  → 使用备用采样率: {rate}Hz")
                                    sample_rate = rate
                                    break
                            except:
                                continue
                        break
        
        if target_device_index is None:
            print("警告: 未找到目标USB设备，使用默认输入设备")
            for i in range(p.get_device_count()):
                dev_info = p.get_device_info_by_index(i)
                if dev_info['maxInputChannels'] > 0:
                    target_device_index = i
                    print(f"使用默认设备: {dev_info['name']}")
                    break
        p.terminate()

        return target_device_index, sample_rate