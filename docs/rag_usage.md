# RAG 系统使用指南

## 架构概览

```
文档 (TXT/MD/PDF 等)
  │
  ▼
加载 (FileLoader / DirectoryLoader)
  │
  ▼
切分 (RecursiveCharacterSplitter)
  │
  ▼
向量化 (EmbeddingClient)
  │
  ▼
存储 (VectorStore / ChromaDB)
  │
  ▼
────────────────────────────────────
      检索时
      │
      ▼
用户问题 ──► 向量化 ──► 向量检索 ──► (可选) ReRank ──► LLM 生成 ──► 答案
```

## 配置

在项目根目录创建 `.env` 文件：

```env
# LLM（用于问答生成）
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-flash

# Embedding（用于向量化，Ollama 示例）
EMBED_BASE_URL=http://localhost:11434/v1
EMBED_MODEL=bge-m3:latest
```

配置项说明：

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | LLM API 密钥 | 空 |
| `DEEPSEEK_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 对话模型 | `deepseek-v4-flash` |
| `EMBED_API_KEY` | Embedding API 密钥（可选） | 同 LLM |
| `EMBED_BASE_URL` | Embedding API 地址 | 同 LLM |
| `EMBED_MODEL` | Embedding 模型 | `text-embedding-3-small` |
| `CHROMA_PATH` | ChromaDB 持久化路径 | `./chroma_db` |

## 摄入文档

```bash
# 摄入单个文件
uv run python scripts/ingest.py --path ./data/sample.txt

# 摄入目录下所有文件
uv run python scripts/ingest.py --path ./data

# 调整切分参数
uv run python scripts/ingest.py --path ./data --chunk-size 300 --chunk-overlap 30

# 指定集合名称（可用于区分不同知识库）
uv run python scripts/ingest.py --path ./data/tech --collection tech-docs

# 仅摄入 .md 文件
uv run python scripts/ingest.py --path ./data --glob "**/*.md"
```

摄入流程日志示例：

```
2026-05-11 18:00:00 [INFO] 加载文档: ./data/sample.txt
2026-05-11 18:00:00 [INFO] 加载了 1 个文档
2026-05-11 18:00:00 [INFO] 切分为 5 个文本块
2026-05-11 18:00:01 [INFO] 生成了 5 个向量（维度: 1024）
2026-05-11 18:00:01 [INFO] 已存储到集合 'documents'，共 5 条
```

## 查询

```bash
# 基本查询
uv run python scripts/query.py --question "RAG 是什么？"

# 调整检索参数
uv run python scripts/query.py --question "什么是 RAG？" --k 10 --rerank-top-k 5

# 禁用 LLM 重排序（仅向量检索，速度更快）
uv run python scripts/query.py --question "RAG 是什么？" --no-rerank
```

## 模块说明

| 模块 | 路径 | 功能 |
|------|------|------|
| 文档加载 | `src/rag/loader/` | 读取 TXT/MD/PY 等文本文件，PDF/DOCX 走 unstructured |
| 文档切分 | `src/rag/splitter/` | 递归字符切分，保留元数据 |
| 向量化 | `src/rag/embed/` | OpenAI API 兼容的嵌入服务 |
| 向量存储 | `src/rag/retriever/store.py` | ChromaDB 持久化封装 |
| 重排序 | `src/rag/retriever/reranker.py` | LLM 精排，提升相关性 |
| 检索编排 | `src/rag/retriever/retriever.py` | 嵌入→检索→重排序 |
| RAG 引擎 | `src/rag/engine.py` | 检索→增强→生成 |

## 代码中使用

```python
from src.llm import LLMClient
from src.rag.embed import EmbeddingClient
from src.rag.engine import RAGEngine
from src.rag.retriever import Retriever, ReRanker, VectorStore

vector_store = VectorStore()
embed_client = EmbeddingClient()
llm = LLMClient()
reranker = ReRanker(llm_client=llm)
retriever = Retriever(
    vector_store=vector_store,
    embed_client=embed_client,
    reranker=reranker,
)
engine = RAGEngine(retriever=retriever, llm=llm)

# 获取答案
answer = engine.query("你的问题")

# 获取答案 + 来源
answer, sources = engine.query_with_sources("你的问题")
```

## 测试建议

1. **先跑单元测试**: `uv run python -m pytest tests/test_rag/ -v`
2. **单文档测试**: 用 `data/sample.txt` 做端到端验证
3. **多文档测试**: 准备 5-10 个不同主题的文档，测试检索准确率
4. **参数调优**: 调整 `chunk_size`、`k`、`rerank_top_k` 观察效果变化
