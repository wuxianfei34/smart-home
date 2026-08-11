"""
MQTT 发布脚本 —— 向指定 Topic 发送消息

用法: python publish.py
前置: 确保 Mosquitto broker 已启动 (mosquitto -v)
"""

import paho.mqtt.client as mqtt
import json
import time

# ========== 配置 ==========
BROKER = "localhost"
PORT = 1883
TOPIC = "home/livingroom/sensor"

# ========== 连接回调 ==========
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"✅ 已连接到 MQTT Broker ({BROKER}:{PORT})")
    else:
        print(f"❌ 连接失败，错误码: {reason_code}")

# ========== 主逻辑 ==========
def main():
    # 创建客户端
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect

    # 连接 broker
    client.connect(BROKER, PORT, keepalive=60)

    # 启动网络循环（非阻塞）
    client.loop_start()

    try:
        # 准备消息（JSON 格式）
        data = {
            "device": "temperature_sensor",
            "value": 26,
            "unit": "celsius",
            "timestamp": time.time()
        }
        payload = json.dumps(data)

        # 发布消息
        result = client.publish(TOPIC, payload, qos=1)
        status = result.rc

        if status == mqtt.MQTT_ERR_SUCCESS:
            print(f"📤 已发送: TOPIC={TOPIC}")
            print(f"   内容: {payload}")
        else:
            print(f"❌ 发送失败，状态码: {status}")

        # 等一秒钟确保消息发完
        time.sleep(1)

    except Exception as e:
        print(f"❌ 出错了: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 已断开连接")


if __name__ == "__main__":
    main()
