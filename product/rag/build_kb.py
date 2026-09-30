import os
import glob
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

KNOWLEDGE_DIR = "knowledge_base"      # 你的知识库目录
CHROMA_DIR = "rag/chroma_db"
CHUNK_SIZE = 256
CHUNK_OVERLAP = 50

print("加载文档...")
docs = []
for pattern, Loader in [("**/*.pdf", PyPDFLoader), ("**/*.docx", Docx2txtLoader)]:
    for f in glob.glob(os.path.join(KNOWLEDGE_DIR, pattern), recursive=True):
        print(f"  {os.path.basename(f)}")
        docs.extend(Loader(f).load())

print(f"共 {len(docs)} 个文档片段")

print("切分...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
)
chunks = splitter.split_documents(docs)
print(f"共 {len(chunks)} 个文本块")

print("向量化（首次会下载模型，约120MB）...")
embeddings = HuggingFaceEmbeddings(
    model_name="/Users/mac/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/e8f8c211226b894fcb81acc59f3b34ba3efd5f42"
)

if os.path.exists(CHROMA_DIR):
    import shutil
    shutil.rmtree(CHROMA_DIR)

print("测试嵌入模型...")
test_vec = embeddings.embed_query("测试文本")
print(f"向量维度：{len(test_vec)}")
if len(test_vec) == 0:
    print("模型没有生成向量！")
    import sys
    sys.exit(1)

vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_DIR)
vectorstore.persist()
print(f"向量库已保存至 {CHROMA_DIR}")