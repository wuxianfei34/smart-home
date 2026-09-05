"""
FastAPI 接口 —— 把智能家居 Agent 包装成 HTTP 服务

启动（从项目根目录运行）:
  venv\\Scripts\\python -m uvicorn src.api.app:app --reload

测试:
  POST http://localhost:8000/chat
  Body: {"msg": "空调显示 E3 怎么办？"}
"""

import sys
from pathlib import Path

# 把 src 目录加入模块搜索路径，才能 import agent.core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from pydantic import BaseModel
from agent.core import build_agent

# 构建 FastAPI 应用
app = FastAPI(title="智能家居 Agent API", version="1.0")

# 启动时构建 Agent（会加载 embedding 模型和向量库，需要几秒）
print("正在加载 Agent（embedding 模型 + 向量库）...")
agent = build_agent()
print("Agent 加载完成")


# ========== 请求/响应模型 ==========
class ChatRequest(BaseModel):
    msg: str  # 用户输入的自然语言


class ChatResponse(BaseModel):
    reply: str  # Agent 的回答


# ========== 接口 ==========
@app.get("/")
def root():
    """健康检查"""
    return {"status": "ok", "message": "智能家居 Agent 服务运行中，POST /chat 提问"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    核心接口：接收自然语言，返回 Agent 回答。
    例：{"msg": "打开客厅灯"} → {"reply": "客厅灯已打开"}
    """
    # 调用 Agent（invoke 一次性返回完整结果）
    result = agent.invoke({"messages": [{"role": "user", "content": req.msg}]})
    reply = result["messages"][-1].content
    return ChatResponse(reply=reply)
