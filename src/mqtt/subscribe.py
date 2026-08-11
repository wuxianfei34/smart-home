"""
MQTT 订阅脚本 —— 监听指定 Topic，收到消息后打印

用法: python subscribe.py
前置: 确保 Mosquitto broker 已启动 (mosquitto -v)
"""

import paho.mqtt.client as mqtt
import json

# ========== 配置 ==========
BROKER = "localhost"
PORT = 1883
TOPIC = "home/livingroom/sensor"

# ========== 回调函数 ==========
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"✅ 已连接到 MQTT Broker ({BROKER}:{PORT})")
        # 订阅 topic
        client.subscribe(TOPIC, qos=1)
        print(f"👂 正在监听: {TOPIC}")
    else:
        print(f"❌ 连接失败，错误码: {reason_code}")


def on_message(client, userdata, msg):
    """收到消息时的回调"""
    topic = msg.topic
    payload_str = msg.payload.decode("utf-8")

    # 尝试解析 JSON
    try:
        payload = json.loads(payload_str)
        print(f"\n📩 收到消息 [{topic}]:")
        print(f"   设备: {payload.get('device', 'unknown')}")
        print(f"   数值: {payload.get('value', '?')} {payload.get('unit', '')}")
    except json.JSONDecodeError:
        # 如果不是 JSON，直接打印原始内容
        print(f"\n📩 收到消息 [{topic}]: {payload_str}")


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    print(f"🔌 已断开连接 (原因码: {reason_code})")


# ========== 主逻辑 ==========
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(BROKER, PORT, keepalive=60)

    print("按 Ctrl+C 停止监听...")
    try:
        # 阻塞式循环，持续监听
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n👋 手动停止")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
