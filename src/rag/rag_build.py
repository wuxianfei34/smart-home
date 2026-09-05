"""
RAG 建库脚本：把设备说明书 PDF 变成「可检索的向量库」

数据流：
  PDF → 提取文本 → 切分成小段 → 每段转成向量(Embedding) → 存入 Chroma

用法（从项目根目录运行）:
  python src/rag/rag_build.py

运行一次即可。改说明书后需重新运行。
"""

import os
from pathlib import Path

# 设置 HuggingFace 镜像（国内下载模型更快），用户已设置则保留
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb

# ========== 路径配置（用项目根目录定位，不依赖运行时的 cwd）==========
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PDF_PATH = PROJECT_ROOT / "docs" / "设备说明书.pdf"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "smart_home_manual"
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"   # 中文 embedding 模型，本地运行


def main():
    print("=" * 50)
    print("  📚 RAG 建库：设备说明书 → 向量库")
    print("=" * 50)

    # ---------- 第 1 步：提取 PDF 文本 ----------
    print(f"\n[1/4] 读取 PDF: {PDF_PATH.name}")
    reader = PdfReader(str(PDF_PATH))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    print(f"   提取到 {len(text)} 个字符")

    # ---------- 第 2 步：文本切分 ----------
    print("\n[2/4] 切分文本（RecursiveCharacterTextSplitter）")
    # chunk_size=200：每段约 200 字；chunk_overlap=40：相邻段重叠 40 字
    # 重叠是为了避免一句话被从中间切断，导致检索时信息不完整
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=40,
        # 切分优先级：先按空行分，再按换行，再按句号/感叹号/问号...
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
    )
    chunks = splitter.split_text(text)
    print(f"   切成 {len(chunks)} 个片段")

    # ---------- 第 3 步：Embedding（文字 → 向量）----------
    print("\n[3/4] 加载 embedding 模型（首次会下载，约 100MB）")
    model = SentenceTransformer(EMBED_MODEL)
    print(f"   模型加载完成，开始把 {len(chunks)} 段转成向量...")
    embeddings = [model.encode(c).tolist() for c in chunks]
    print("   向量转换完成")

    # ---------- 第 4 步：存入 Chroma ----------
    print("\n[4/4] 写入 Chroma 向量库")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 清空旧库（避免重复建库时数据叠加）
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        collection.add(
            documents=[chunk],
            embeddings=[emb],
            ids=[f"chunk_{i}"],
        )

    print(f"\n✅ 建库完成！{len(chunks)} 个片段已存入 {CHROMA_DIR}")
    print(f"   接下来可以运行 rag_query.py 提问了")


if __name__ == "__main__":
    main()
