from langchain_core.tools import tool
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 全局加载一次（用你本地缓存路径）
_embeddings = HuggingFaceEmbeddings(
    model_name="/Users/mac/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
)
_vectorstore = Chroma(
    persist_directory="rag/chroma_db",
    embedding_function=_embeddings,
)


@tool
def search_knowledge_base(query: str, k: int = 3) -> str:
    """
    从数据中心能耗知识库中检索相关段落。
    知识库包含：GB 40879-2021、YD/T 6232-2024、发改委能效通知、节能基础知识手册。
    
    参数：
    - query: 检索问题（如"PUE的能效等级怎么划分"）
    - k: 返回的段落数量，默认3
    """
    docs = _vectorstore.similarity_search(query, k=k)
    if not docs:
        return "知识库中未找到相关内容"
    
    result = f"检索到 {len(docs)} 个相关段落：\n\n"
    for i, doc in enumerate(docs, 1):
        result += f"【段落{i}】\n{doc.page_content}\n\n"
    return result