"""
Agent 核心模块：构建 LLM + 工具 + Agent

供两个入口复用：
  - src/agent/smart_agent.py   （命令行测试）
  - src/api/app.py              （FastAPI HTTP 接口）

好处：Agent 构建逻辑只写一份，改一处两处都生效。
"""

import os
import time
from pathlib import Path

# 加载 .env（API Key）+ 设置 HF 镜像（embedding 模型）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
from dotenv import load_dotenv
load_dotenv()

import paho.mqtt.client as mqtt
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from sentence_transformers import SentenceTransformer
import chromadb


# ================================================================
# 配置
# ================================================================
BROKER = "localhost"
PORT = 1883

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "smart_home_manual"
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"

DEVICE_TOPICS = {
    "客厅灯": "home/livingroom/led",
}


# ================================================================
# LLM
# ================================================================
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0,
)


# ================================================================
# RAG 组件（加载一次，供 search_manual 工具使用）
# ================================================================
embed_model = SentenceTransformer(EMBED_MODEL)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_collection(COLLECTION_NAME)


# ================================================================
# MQTT 底层发布
# ================================================================
def _mqtt_publish(topic: str, payload: str) -> str:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
        result = client.publish(topic, payload, qos=1)
        time.sleep(0.5)
        client.loop_stop()
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return f"成功：已向 {topic} 发送指令 {payload}"
        return f"失败：发送到 {topic} 出错"
    except Exception as e:
        return f"失败：MQTT 连接异常 {e}"
    finally:
        client.disconnect()


# ================================================================
# 三个工具
# ================================================================
@tool
def control_device(device: str, action: str) -> str:
    """
    控制智能家居设备的开关。
    当用户说"打开/关闭某设备"时，调用此工具。
    参数:
        device: 设备名称，只能是 "客厅灯"
        action: 操作指令，只能是 "on"（开）或 "off"（关）
    """
    if device not in DEVICE_TOPICS:
        return f"错误：未知设备 {device}，可选设备：{list(DEVICE_TOPICS.keys())}"
    if action not in ("on", "off"):
        return f"错误：未知操作 {action}，只能是 on 或 off"
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


@tool
def search_manual(question: str) -> str:
    """
    查询智能家居设备说明书（RAG 检索）。
    当用户询问设备的使用方法、故障码含义、参数规格、常见问题时，调用此工具。
    参数:
        question: 用户想要查询的具体问题，如"空调显示E3怎么办"
    """
    q_embedding = embed_model.encode(question).tolist()
    result = collection.query(query_embeddings=[q_embedding], n_results=3)
    contexts = result["documents"][0]
    return "检索到的说明书片段：\n" + "\n".join(f"- {c}" for c in contexts)


# ================================================================
# 构建 Agent（供外部调用）
# ================================================================
def build_agent():
    """组装一个完整 Agent：控灯 + 查温度 + 查手册"""
    tools = [control_device, get_temperature, search_manual]
    return create_agent(llm, tools)
