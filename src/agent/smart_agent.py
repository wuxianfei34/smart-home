"""
命令行测试入口 —— 复用 core.py 的 build_agent()

用法（从项目根目录运行，需已跑过 rag_build.py 建库）:
  python src/agent/smart_agent.py
"""

from core import build_agent

agent = build_agent()


def ask(question: str):
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
            brief = content[:80] + ("..." if len(content) > 80 else "")
            print(f"   🔧 调用工具 [{tool_name}] → {brief}")


if __name__ == "__main__":
    print("=" * 50)
    print("  🏠 智能家居完整 Agent（控灯 + 查温度 + 查手册）")
    print("=" * 50)

    ask("把客厅灯打开")
    ask("空调显示 E3 怎么办？")
    ask("客厅灯连不上 WiFi 怎么办？")
    ask("客厅现在多少度？")
