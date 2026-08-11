"""
模拟智能家居设备 —— 订阅 MQTT 指令，模拟真实设备行为

当前支持的模拟设备：
  - 客厅灯: home/livingroom/led → "on" / "off"
  - 传感器: home/livingroom/sensor → 温度数据

用法: python fake_device.py
前置: 确保 Mosquitto broker 已启动 (mosquitto -v)
"""

import paho.mqtt.client as mqtt
import json
import time

# ========== 配置 ==========
BROKER = "localhost"
PORT = 1883

# 设备订阅列表
DEVICES = {
    "客厅灯": {
        "topic": "home/livingroom/led",
        "state": "off",
    },
    "客厅传感器": {
        "topic": "home/livingroom/sensor",
        "state": None,
    },
}


# ========== 回调函数 ==========
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"✅ 设备模拟器已连接到 MQTT Broker")
        # 订阅所有设备 topic
        for name, cfg in DEVICES.items():
            client.subscribe(cfg["topic"], qos=1)
            print(f"   👂 {name} → {cfg['topic']}")
    else:
        print(f"❌ 连接失败: {reason_code}")


def on_message(client, userdata, msg):
    """收到控制指令"""
    topic = msg.topic
    payload_str = msg.payload.decode("utf-8")

    # 找到对应设备
    device_name = None
    for name, cfg in DEVICES.items():
        if cfg["topic"] == topic:
            device_name = name
            break

    if device_name is None:
        print(f"⚠️  未知 topic: {topic}")
        return

    # 处理指令
    if topic == "home/livingroom/led":
        if payload_str == "on":
            DEVICES["客厅灯"]["state"] = "on"
            print(f"💡 客厅灯 → 已打开")
        elif payload_str == "off":
            DEVICES["客厅灯"]["state"] = "off"
            print(f"💡 客厅灯 → 已关闭")
        else:
            print(f"⚠️  未知指令: {payload_str}")

    elif topic == "home/livingroom/sensor":
        try:
            data = json.loads(payload_str)
            print(f"🌡️  传感器数据: {data}")
        except json.JSONDecodeError:
            print(f"📊 传感器原始数据: {payload_str}")


def on_disconnect(client, userdata, flags, reason_code, properties=None):
    print(f"🔌 设备模拟器已断开")


# ========== 主逻辑 ==========
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect(BROKER, PORT, keepalive=60)

    print("🏠 智能家居设备模拟器已启动")
    print("   按 Ctrl+C 停止...")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n👋 设备模拟器已停止")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
