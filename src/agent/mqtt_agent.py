"""
迷你 Demo（第 5-6 周）：自然语言 → Agent → MQTT 控制智能家居设备

端到端链路：
  用户说 "打开客厅灯"
    → LangChain Agent 判断该调 control_device 工具
    → control_device 发 MQTT 消息 "on" 到 home/livingroom/led
    → fake_device.py 收到后打印 "💡 客厅灯 → 已打开"

运行步骤（开 3 个终端）：
  终端1: mosquitto -v                          # 启动 MQTT broker
  终端2: python -u src/mqtt/fake_device.py      # 启动设备模拟器
  终端3: python -u src/agent/mqtt_agent.py      # 跑 Agent（本脚本）
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 里的 API Key

import paho.mqtt.client as mqtt
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent


# ================================================================
# 配置
# ================================================================
BROKER = "localhost"
PORT = 1883

# 设备映射表：中文设备名 → MQTT topic
# 这是"翻译层"：把人类语言里的"客厅灯"，翻译成设备能听懂的 topic 地址
# 以后要加设备（空调、音响），在这里加一行就行
DEVICE_TOPICS = {
    "客厅灯": "home/livingroom/led",
    # "卧室灯": "home/bedroom/led",      # 预留：后续可扩展
    # "客厅空调": "home/livingroom/ac",   # 预留
}


# ================================================================
# 第 1 步：定义 LLM
# ================================================================
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0,  # 0 = 只要准确，不要创意
)


# ================================================================
# 第 2 步：MQTT 发布底层函数（真正的"干活"代码）
# ================================================================
def _mqtt_publish(topic: str, payload: str) -> str:
    """
    实际执行 MQTT 发布：连接 broker → 发消息 → 断开。
    这个函数不是 Tool，它是被 Tool 调用的"底层能力"。
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()                     # 启动后台网络循环
        result = client.publish(topic, payload, qos=1)  # qos=1 至少送达一次
        time.sleep(0.5)                         # 等消息发出去
        client.loop_stop()

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return f"成功：已向 {topic} 发送指令 {payload}"
        return f"失败：发送到 {topic} 出错，错误码 {result.rc}"
    except Exception as e:
        return f"失败：MQTT 连接异常 {e}"
    finally:
        client.disconnect()


# ================================================================
# 第 3 步：定义 Tool（Agent 的"手"）
# ================================================================
# 关键设计：这里用"语义化"工具 control_device，而不是直接暴露 mqtt_publish。
# 因为 LLM 需要知道"我能干什么"，而不是"怎么发消息"。
# docstring 是写给 LLM 看的说明书，决定它会不会正确调用。


@tool
def control_device(device: str, action: str) -> str:
    """
    控制智能家居设备的开关。
    当用户说"打开/关闭某设备"时，调用此工具。

    参数:
        device: 设备名称，只能是 "客厅灯"
        action: 操作指令，只能是 "on"（开）或 "off"（关）
    """
    # 校验设备是否存在（防止 LLM 乱传参数）
    if device not in DEVICE_TOPICS:
        return f"错误：未知设备 {device}，可选设备：{list(DEVICE_TOPICS.keys())}"

    # 校验操作是否合法
    if action not in ("on", "off"):
        return f"错误：未知操作 {action}，只能是 on 或 off"

    # 把设备名翻译成 topic，然后发 MQTT 消息
    topic = DEVICE_TOPICS[device]
    return _mqtt_publish(topic, action)


@tool
def get_temperature(location: str = "客厅") -> str:
    """
    获取指定位置的当前温度。
    当用户询问温度、热不热、冷不冷时，调用此工具。
    """
    fake_data = {"客厅": 26, "卧室": 24, "阳台": 32, "厨房": 28}
    temp = fake_data.get(location, 25)
    return f"{location}当前温度是 {temp}°C"


# ================================================================
# 第 4 步：注册工具 + 创建 Agent
# ================================================================
tools = [control_device, get_temperature]

# create_agent（新版 API，替代已弃用的 create_react_agent）
# Agent 会循环执行：思考 → 调工具 → 观察结果 → 再思考 → 直到能回答
agent = create_agent(llm, tools)


# ================================================================
# 第 5 步：交互测试
# ================================================================
def ask(question: str):
    """向 Agent 提问，流式打印它调了哪些工具、怎么回答"""
    print(f"\n{'='*50}")
    print(f"🧑 用户: {question}")
    print(f"{'='*50}")

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        last_msg = chunk["messages"][-1]
        role = getattr(last_msg, "type", "?")
        content = getattr(last_msg, "content", "")

        if role == "ai" and content:
            print(f"\n🤖 Agent: {content}")
        elif role == "tool":
            tool_name = getattr(last_msg, "name", "unknown")
            print(f"   🔧 调用工具 [{tool_name}] → {content}")


if __name__ == "__main__":
    print("=" * 50)
    print("  🏠 智能家居 Agent（Agent + MQTT 迷你 Demo）")
    print("  LLM: DeepSeek V3 | 设备: 客厅灯")
    print("=" * 50)

    # 测试 1：开灯（核心验收）
    ask("把客厅灯打开")

    # 测试 2：关灯
    ask("关闭客厅灯")

    # 测试 3：查询温度（证明 Agent 既能控制也能查询）
    ask("客厅现在多少度？")
