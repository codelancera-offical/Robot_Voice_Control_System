"""
WebSocket 测试脚本 V2.0
"""

import websocket
import socket

# 解析 dashscope 的 IPv4 地址（避免使用 IPv6）
ipv4_addr = socket.gethostbyname('dashscope.aliyuncs.com')

# 手动建立 IPv4 socket
sock = socket.create_connection((ipv4_addr, 443), timeout=10)

# 建立 WebSocket over the already-created socket（指定 server_hostname 用于 TLS）
try:
    ws = websocket.create_connection(
        "wss://dashscope.aliyuncs.com",
        sock=sock,
        timeout=10,
        server_hostname='dashscope.aliyuncs.com'  # 重要：用于 SSL 证书验证
    )
    print("✅ 成功使用 IPv4 建立 WebSocket 连接")
    ws.close()
except Exception as e:
    print("❌ 连接失败：", e)