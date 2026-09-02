"""
第 3-4 周验收脚本：LLM Agent 调用自定义 Tool

目标：Agent 收到"现在多热？" → 自动调用 get_temperature() → 回答温度

用法:
  1. 把 DeepSeek API Key 写入 .env 文件（DEEPSEEK_API_KEY=xxx）
  2. python src/agent/hello_agent.py
"""

import os
from dotenv import load_dotenv

# 加载 .env 里的 API Key
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


# ================================================================
# 第 1 步：定义 LLM（用 DeepSeek，OpenAI 兼容接口）
# ================================================================
llm = ChatOpenAI(
    model="deepseek-chat",                         # DeepSeek V3 模型
    api_key=os.getenv("DEEPSEEK_API_KEY"),          # 从 .env 读取
    base_url=os.getenv("DEEPSEEK_BASE_URL"),        # DeepSeek 的 API 地址
    temperature=0,                                   # 0 = 不要创意，只要准确
)


# ================================================================
# 第 2 步：定义 Tool —— 这是 Agent 的"手"
# ================================================================
# @tool 装饰器会自动把函数签名和 docstring 转成 LLM 能理解的 Tool 描述
# LLM 不执行这个函数，它只是"决定"要不要调、传什么参数


@tool
def get_temperature(location: str = "客厅") -> str:
    """
    获取指定位置的当前温度。
    当用户询问温度、热不热、冷不冷时，调用此工具。

    参数:
        location: 位置名称，如 "客厅"、"卧室"、"阳台"
    """
    # 模拟：实际项目中这里接真实传感器或 API
    fake_data = {
        "客厅": 26,
        "卧室": 24,
        "阳台": 32,
        "厨房": 28,
    }
    temp = fake_data.get(location, 25)
    return f"{location}当前温度是 {temp}°C"


@tool
def get_humidity(location: str = "客厅") -> str:
    """
    获取指定位置的当前湿度。
    当用户询问湿度、潮不潮时，调用此工具。

    参数:
        location: 位置名称
    """
    fake_data = {"客厅": 55, "卧室": 60, "阳台": 40, "厨房": 50}
    humidity = fake_data.get(location, 50)
    return f"{location}当前湿度是 {humidity}%"


# ================================================================
# 第 3 步：把所有 Tool 注册给 Agent
# ================================================================
tools = [get_temperature, get_humidity]


# ================================================================
# 第 4 步：创建 Agent（用 LangGraph 的 ReAct 模式）
# ================================================================
# ReAct = Reasoning + Acting，大模型会循环执行：
#   Thought（思考要干什么）→ Action（调哪个 Tool）→ Observation（Tool 返回结果）
#   重复直到能回答用户问题

agent = create_react_agent(llm, tools)


# ================================================================
# 第 5 步：测试
# ================================================================
def ask(question: str):
    """向 Agent 提问并流式打印结果"""
    print(f"\n{'='*50}")
    print(f"🧑 用户: {question}")
    print(f"{'='*50}")

    # stream_mode="values" 展示每一步中间状态
    # 可以看到 Agent 的思考过程
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        # 只打印最后一条消息
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
    print("  🤖 LangChain Agent 入门脚本")
    print("  LLM: DeepSeek V3 | 模式: ReAct")
    print("=" * 50)

    # 测试 1：单 Tool 调用（验收标准）
    ask("现在客厅有多热？")

    # 测试 2：多 Tool 调用
    ask("客厅的温度和湿度分别是多少？")

    # 测试 3：不需要 Tool 的普通对话
    ask("你是谁？")
