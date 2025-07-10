#!/bin/bash

# --- PipeWire/ALSA 详细诊断脚本 ---
# 这个脚本用于收集 Linux 系统上 PipeWire 和 ALSA 相关的配置和状态信息。
# 请在两台机器上都运行此脚本，并将完整的输出提供给分析。

echo "--- 1. 系统信息 ---"
uname -a
lsb_release -d 2>/dev/null || cat /etc/*release
echo "---"

echo "--- 2. PipeWire/PulseAudio 进程状态 ---"
echo "PipeWire 主进程:"
pgrep -a pipewire
echo "PipeWire 会话管理器 (WirePlumber/Media Session):"
pgrep -a wireplumber || pgrep -a pipewire-media-session
echo "---"

echo "--- 3. PulseAudio 信息 (pactl info) ---"
pactl info
echo "---"

echo "--- 4. PulseAudio 模块列表 (pactl list modules) ---"
pactl list modules
echo "---"

echo "--- 5. ALSA 声卡列表 (aplay -l) ---"
aplay -l
echo "---"

echo "--- 6. ALSA 录音设备列表 (arecord -l) ---"
arecord -l
echo "---"

echo "--- 7. ALSA 设备信息 (alsamixer -c <card_number> -V all 的简要输出，选择 USB 声卡) ---"
# 尝试查找 USB 声卡号
USB_CARD_NUM=$(arecord -l | grep -i "USB PnP Audio Device" | sed -n 's/card \([0-9]*\):.*/\1/p' | head -n 1)
if [ -n "$USB_CARD_NUM" ]; then
    echo "检测到 USB 声卡号: card $USB_CARD_NUM"
    amixer -c $USB_CARD_NUM scontents
else
    echo "未检测到 USB 声卡。将显示默认声卡或跳过此步骤。"
    amixer scontents # 尝试显示默认声卡
fi
echo "---"

echo "--- 8. PipeWire 默认配置文件内容 (/etc/pipewire/pipewire.conf) ---"
if [ -f /etc/pipewire/pipewire.conf ]; then
    cat /etc/pipewire/pipewire.conf
else
    echo "文件 /etc/pipewire/pipewire.conf 不存在。"
fi
echo "---"

echo "--- 9. PipeWire PulseAudio 桥接配置文件内容 (/etc/pipewire/pipewire-pulse.conf) ---"
if [ -f /etc/pipewire/pipewire-pulse.conf ]; then
    cat /etc/pipewire/pipewire-pulse.conf
else
    echo "文件 /etc/pipewire/pipewire-pulse.conf 不存在。"
fi
echo "---"

echo "--- 10. PipeWire 会话管理器配置文件内容 (/etc/pipewire/media-session.d/*.conf 或 /etc/pipewire/wireplumber.conf) ---"
# 检查 WirePlumber 配置
if [ -f /etc/pipewire/wireplumber.conf ]; then
    echo "检测到 WirePlumber 配置文件:"
    cat /etc/pipewire/wireplumber.conf
elif [ -d /etc/pipewire/media-session.d/ ]; then
    echo "检测到 pipewire-media-session 配置目录，列出所有 .conf 文件内容:"
    find /etc/pipewire/media-session.d/ -name "*.conf" -exec echo "--- {} ---" \; -exec cat {} \;
else
    echo "未检测到 WirePlumber 或 pipewire-media-session 系统级配置文件。"
fi
echo "---"

echo "--- 11. PulseAudio 默认配置文件内容 (/etc/pulse/default.pa) ---"
if [ -f /etc/pulse/default.pa ]; then
    cat /etc/pulse/default.pa
else
    echo "文件 /etc/pulse/default.pa 不存在。"
fi
echo "---"

echo "--- 12. 用户级 PipeWire 配置文件 (~/.config/pipewire/*.conf 或 ~/.config/pipewire-pulse/*.conf) ---"
if [ -d ~/.config/pipewire ]; then
    find ~/.config/pipewire -name "*.conf" -exec echo "--- {} ---" \; -exec cat {} \;
else
    echo "目录 ~/.config/pipewire 不存在。"
fi
if [ -d ~/.config/pipewire-pulse ]; then
    find ~/.config/pipewire-pulse -name "*.conf" -exec echo "--- {} ---" \; -exec cat {} \;
else
    echo "目录 ~/.config/pipewire-pulse 不存在。"
fi
echo "---"

echo "--- 13. ALSA 用户配置文件内容 (~/.asoundrc) ---"
if [ -f ~/.asoundrc ]; then
    cat ~/.asoundrc
else
    echo "文件 ~/.asoundrc 不存在。"
fi
echo "---"

echo "--- 14. ALSA 系统配置文件内容 (/etc/asound.conf) ---"
if [ -f /etc/asound.conf ]; then
    cat /etc/asound.conf
else
    echo "文件 /etc/asound.conf 不存在。"
fi
echo "---"

echo "--- 15. 用户所在组 ---"
groups $(whoami)
echo "---"


echo "诊断结束。"systemctl --user daemon-reload