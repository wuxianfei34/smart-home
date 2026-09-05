"""
RAG 查询脚本：问题 → 检索相关片段 → 拼进 prompt → LLM 回答

数据流：
  问题 → Embedding → Chroma 检索 Top-K 片段 → 拼 prompt → DeepSeek 回答

用法（从项目根目录运行，需先跑过 rag_build.py）:
  python src/rag/rag_query.py
"""

import os
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
import chromadb
from langchain_openai import ChatOpenAI

# ========== 配置 ==========
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "smart_home_manual"
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"


# ========== 加载模型 + 向量库 + LLM（只加载一次）==========
print("正在加载 embedding 模型和向量库...")
embed_model = SentenceTransformer(EMBED_MODEL)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_collection(COLLECTION_NAME)

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0,
)


def ask(question: str, top_k: int = 3):
    """
    完整 RAG 流程：
      1. 问题转向量
      2. 在向量库检索最相似的 top_k 个片段
      3. 把片段拼进 prompt
      4. 交给 LLM 生成回答
    """
    print(f"\n{'='*50}")
    print(f"🧑 提问: {question}")
    print(f"{'='*50}")

    # 第 1 步：问题 → 向量
    q_embedding = embed_model.encode(question).tolist()

    # 第 2 步：检索
    result = collection.query(
        query_embeddings=[q_embedding],
        n_results=top_k,
    )
    contexts = result["documents"][0]

    # 打印检索到的片段（让你看到 RAG 到底"找到"了什么）
    print(f"\n📌 检索到 {len(contexts)} 个相关片段：")
    for i, ctx in enumerate(contexts, 1):
        print(f"   [{i}] {ctx[:60]}...")

    # 第 3 步：拼 prompt（关键：把检索内容塞给 LLM）
    prompt = f"""你是智能家居客服助手。请根据下面提供的资料回答问题。
如果资料中没有答案，请诚实地说"资料中没有相关信息"，不要编造。

【资料】
{chr(10).join(f"- {c}" for c in contexts)}

【问题】
{question}
"""
    # 第 4 步：LLM 回答
    response = llm.invoke(prompt)
    print(f"\n🤖 回答: {response.content}")


if __name__ == "__main__":
    print("=" * 50)
    print("  🤖 RAG 智能家居手册问答")
    print("=" * 50)

    # 测试 1：故障码（验收题）
    ask("空调显示 E3 怎么办？")

    # 测试 2：灯的常见问题
    ask("客厅灯连不上 WiFi 怎么办？")

    # 测试 3：传感器参数
    ask("温湿度传感器的测量精度是多少？")

    # 测试 4：资料外的问题（考验 RAG 会不会诚实说不知道）
    ask("空调能放音乐吗？")
