
# 数据中心能耗智能问答助手

基于 LangChain + LLM API，面向不熟悉内部命名规则的客户，用自然语言回答数据中心能耗相关问题。支持数据发现、统计分析、PUE测算、知识问答、自动出图。

包含以下核心模块：

- `chat.py`：终端对话入口，适合快速测试和调试
- `app.py`：Streamlit 网页入口，支持图表渲染，适合演示
- `rag/build_kb.py`：构建知识库向量库（一次性运行）

---

## 整体架构

```
用户提问（自然语言）
        ↓
LangChain Agent（LLM 驱动）
判断意图 → 决定调用哪个工具
        ↓
┌────────┬────────┬────────┬────────┐
│ 数据发现 │ 通用分析 │ 专用分析 │ 计算   │
└────────┴────────┴────────┴────────┘
        ↓
RAG 知识库（Chroma + 本地嵌入模型）
GB 40879 / YD/T 6232 / 节能手册
        ↓
文字回答 + 图表
```

---

## 目录结构

```
成品/
├── chat.py                      终端对话入口
├── app.py                       Streamlit 网页入口
├── requirements.txt
├── data_model/
│   ├── table_parser.py          表名解析
│   └── data_scanner.py          目录扫描、文件索引
├── analysis/
│   └── meter_analyzer.py        表计数据统计分析
├── tools/
│   ├── meter_tools.py           表计解析、目录扫描、文件查找
│   ├── generic_data_tools.py    通用数据分析
│   ├── data_discovery.py        数据目录探索
│   ├── calc_tools.py            PUE 测算
│   ├── rag_tools.py             知识库检索
│   ├── data_dict_tools.py       数据字典查询
│   ├── viz_tools.py             表计趋势图
│   └── generic_viz_tools.py     通用可视化
├── rag/
│   ├── build_kb.py              向量库构建脚本
│   ├── chroma_db/               向量库（构建后生成）
│   └── knowledge_base/          原始文档（PDF/DOCX）
└── models/
    └── bge-small-zh-v1.5/       本地嵌入模型
```

---

## 本地环境配置

按顺序执行以下步骤。

### 步骤 1：安装 Python 依赖

```bash
cd "你的目标目录"
pip3 install -r requirements.txt --user
```

requirements.txt 内容：

```
streamlit>=1.30
langchain>=0.1.0
langchain-openai>=0.1.0
langchain-community>=0.1.0
chromadb>=0.4.22
sentence-transformers>=2.3.0
huggingface-hub>=0.20.0
pandas>=2.0
numpy<2
matplotlib>=3.7
openpyxl>=3.1
docx2txt
pypdf
```

关键点：numpy 必须锁在 2.0 以下，否则 PyTorch 会报 `Numpy is not available`。

### 步骤 2：准备嵌入模型

推荐方案：从 ModelScope 下载中文专用模型。

```bash
pip3 install modelscope --user
modelscope download --model BAAI/bge-small-zh-v1.5 --local_dir ./models/bge-small-zh-v1.5
```

然后把 `rag/build_kb.py` 和 `tools/rag_tools.py` 里的 model_name 改成：

```python
model_name="./models/bge-small-zh-v1.5"
```

备选方案：如果你之前已经从 Hugging Face 下载过模型，可以用缓存路径。先找到缓存目录：

```bash
ls ~/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/
```

记下哈希值目录，在代码里用这个绝对路径。

### 步骤 3：配置 LLM API

在 `chat.py` 和 `app.py` 里配置模型。目前用的是 DeepSeek：

```python
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    api_key="sk-你的DeepSeek密钥",
    temperature=0.3,
)
```

如果没有 DeepSeek 额度，可以换成阿里云百炼：

```python
llm = ChatOpenAI(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="sk-你的阿里云百炼Key",
    temperature=0.3,
)
```

### 步骤 4：构建知识库向量库

把 GB 40879、YD/T 6232、发改委通知、节能手册放到 `rag/knowledge_base/`，然后运行：

```bash
cd "你的目标目录""
python3 rag/build_kb.py
```

成功后会生成 `rag/chroma_db/`。

### 步骤 5：确认数据目录

在 `chat.py` 里设置数据目录：

```python
DATA_DIR = "/你的目标目录""
```

确认目录存在：

```bash
ls "$DATA_DIR"
```

---

## 启动方式

### 终端模式

```bash
cd "/Users/mac/Documents/Caden/2026年暑假实习项目/成品"
python3 chat.py
```

### 网页模式（推荐）

```bash
streamlit run app.py
```

浏览器自动打开 http://localhost:8501。

---

## 能问什么

### 数据发现类

- 我有哪些数据？
- fdds 园区有什么数据？
- sjzskfu 园区有哪些分项？

### 数据分析类

- 帮我分析一下 fdds 园区的用电情况
- 哪个分项最耗电？
- 有没有异常数据？
- 按园区对比一下用电量

### 计算类

- IT功率500kW，PUE从1.6降到1.3，电价0.65，一年省多少钱？
- 当前PUE 1.5，目标1.25，投资80万，回收期多久？

### 知识问答类

- PUE的能效等级是怎么划分的？
- 冷热通道封闭的节能率是多少？
- GB 40879 对新建数据中心的要求是什么？

### 可视化类

- 帮我画一下 fdds 园区的用电趋势
- 按分项对比一下用电量

---

## 关键参数调优

**max_iterations**（在 chat.py 里）

Agent 最大推理步数。默认 15。
- 调大：能处理更复杂的多步问题，但可能陷入循环
- 调小：响应快，但复杂问题会中途停止

**temperature**（在 chat.py 里）

模型输出随机性。默认 0.3。
- 调大：回答更多样，但可能不准确
- 调小：回答更稳定，但可能死板

**chunk_size**（在 rag/build_kb.py 里）

知识库切分粒度。默认 256。
- 调大：每块内容更多，但检索精度下降
- 调小：检索更精准，但可能丢失上下文

默认值已测试验证：对常规问题，Agent 能在 5 步内完成；对"分析整个园区"这类开放问题，15 步足够。如遇循环，可继续调大。

---

## 让助手效能最大化的关键配置

**第一，数据目录要规范。**

Agent 的"数据发现"能力完全依赖文件名规范。确保数据文件遵循以下命名：

```
meter_cfg_${tcode}_${pcode}_${cfg_id}_${period}.csv
meter_incr_${tcode}_${pcode}_${flow_num}_${flag}_${period}.csv
meter_original_${tcode}_${pcode}_${flow_num}_${flag}.csv
```

如果文件名不规范，Agent 无法识别，会退化成"通用文件分析"模式，效果下降。

**第二，数据字典要完整。**

数据字典信息表里的字段说明越详细，Agent 回答"flow_num 是什么"这类问题时越准确。

**第三，知识库文档要齐全。**

rag/knowledge_base/ 里放的文档越全，Agent 回答标准类问题时越可靠。

**第四，System Prompt 要贴合业务。**

chat.py 里的 SYSTEM_PROMPT 定义了 Agent 的行为准则。如果你的业务有特殊规则（比如特定园区的默认电价、特定的改造方案），在这里补充。

**第五，模型选择要平衡。**

- DeepSeek-chat：工具调用稳定性高，速度中，成本低
- qwen-plus：工具调用稳定性高，速度中，成本低
- qwen2.5:7b（本地）：工具调用稳定性中，速度慢，免费
- qwen2.5:3b（本地）：工具调用稳定性低，速度快，免费

建议：开发测试用 DeepSeek 或 qwen-plus，演示可以用本地模型。

---

## 常见问题排查

**Numpy is not available**

原因：NumPy 2.x 与 PyTorch 不兼容。
解决：`pip install "numpy<2"`

**Expected Embeddings to be non-empty**

原因：嵌入模型没加载成功。
解决：检查模型路径，确认文件完整。

**max iterations 停止**

原因：Agent 陷入循环。
解决：增大 max_iterations，或缩小分析范围。

**工具调用参数错乱**

原因：ReAct 格式解析问题。
解决：用 create_tool_calling_agent 而非 create_react_agent。

**中文图表乱码**

原因：字体缺失。
解决：代码里已改用英文标签，或安装中文字体。

**docx2txt 缺失**

原因：未装 Word 解析依赖。
解决：`pip3 install docx2txt --user`

**Hugging Face 连不上**

原因：网络限制。
解决：设置 `export HF_ENDPOINT=https://hf-mirror.com`，或用 ModelScope 下载。

---

## 扩展方向

- 接入真实数据库：把 SQL dump 导入 PostgreSQL，让 Agent 直接查库而非读 CSV
- 实时数据流：接入 Kafka 或 MQTT，支持实时监控问答
- 多用户支持：加用户认证，每个用户只能访问自己的数据
- 报告生成：自动生成 PDF 或 Word 格式的能耗分析报告
- 预测分析：加入时间序列预测模型，回答"下个月用电量大概多少"

---

## 文件清单

- chat.py：终端对话主程序
- app.py：Streamlit 网页入口
- rag/build_kb.py：构建知识库向量库
- data_model/table_parser.py：解析数据文件名
- data_model/data_scanner.py：扫描数据目录
- analysis/meter_analyzer.py：表计数据统计
- tools/*.py：各类 LangChain 工具
- requirements.txt：Python 依赖清单

---

## 最后提醒

这套系统是工具集，不是"全自动 AI"。它的效果取决于：

1. 数据文件的命名是否规范
2. 数据字典是否完整
3. 知识库文档是否齐全
4. System Prompt 是否贴合业务
5. 用户提问是否清晰

把这五点做到位，助手就能发挥最大效能。