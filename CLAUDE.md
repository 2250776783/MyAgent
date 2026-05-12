# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人问答助手项目，目标是通过实践学习 **RAG** 和 **Agent** 相关知识。

**当前状态**: 核心功能已实现，Agent 记忆系统 (`src/agent/memory/`) 和规划模块 (`src/agent/planner/`) 仍为空骨架。

## 技术栈

- Python 3.11+, 包管理使用 `uv`
- LLM: OpenAI API 兼容模式，生产使用 DeepSeek v4 flash（通过 DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL 配置）
- 向量数据库: ChromaDB（持久化到 `./chroma_db`）
- 文档处理: unstructured + langchain-text-splitters
- 网页搜索: SerpApi (`google-search-results`)
- 代码质量: ruff (lint+format) + mypy

## 开发命令

```bash
# 安装依赖（含 dev）
uv sync --dev

# 运行所有测试
uv run pytest

# 运行单个测试
uv run pytest tests/test_rag/test_retriever.py

# Lint 检查
uv run ruff check src/

# 自动格式化
uv run ruff format src/

# 类型检查
uv run mypy src/

# 文档摄入
uv run python scripts/ingest.py --path ./data/sample.txt

# RAG 查询
uv run python scripts/query.py --question "你的问题"

# 交互式 Agent 对话（Windows 需 PYTHONIOENCODING=utf-8 避免 GBK 编码错误）
PYTHONIOENCODING=utf-8 uv run python scripts/chat.py
```

## 项目架构与关键实现

```
src/
├── config/settings.py    # pydantic-settings 配置，自动读取 .env
├── llm/                  # LLM 调用封装（已实现）
│   ├── client.py         # LLMClient: 同步/流式 chat，tool calling，重试
│   ├── types.py          # Message: role/content/tool_calls/reasoning_content
│   └── tokenizer.py      # TokenCounter: tiktoken 计数，无 tiktoken 时字符估算
├── rag/                  # RAG 流程（已实现）
│   ├── loader/loader.py  # FileLoader, DirectoryLoader, Document
│   ├── splitter/         # RecursiveCharacterSplitter
│   ├── embed/embedder.py # EmbeddingClient: OpenAI 兼容嵌入
│   ├── retriever/        # VectorStore(ChromaDB), ReRanker(LLM), Retriever(编排)
│   └── engine.py         # RAGEngine: 检索→增强→生成
├── agent/
│   ├── agent.py          # Agent 主类（OpenAI function calling ReAct 循环）
│   ├── tools/            # 两种工具系统并存
│   │   ├── base.py       # BaseTool 抽象基类 + ToolRegistry
│   │   ├── builtin.py    # CalculatorTool, CurrentTimeTool, SearchTool
│   │   ├── search.py     # 独立 SerpApi 搜索函数（被 ToolExecutor 使用）
│   │   └── ToolExecutor.py # 文本 Action/Observation 式工具执行器
│   ├── memory/__init__.py    # 空骨架（待实现）
│   └── planner/__init__.py   # 空骨架（待实现）
scripts/
├── chat.py               # Agent 交互式对话
├── ingest.py             # RAG 数据摄入
└── query.py              # RAG 知识库查询
tests/
├── test_rag/             # 各 RAG 子模块测试
└── test_agent/           # 工具 + Agent 测试
```

## 关键约定与注意事项

### 配置规则
- 所有配置通过 `src.config.settings` 导入（pydantic-settings 自动读取 `.env`）
- `.env` 中的变量**不会**注入 `os.environ`，必须通过 `settings` 对象读取
- `.env` 示例见 `.env.example`

### LLM 兼容性
- 默认使用 DeepSeek v4 flash（支持 thinking/reasoning 模式）
- DeepSeek API 返回 `reasoning_content` 字段，Message 类型已包含该字段并在 `to_dict()` 中序列化
- DeepSeek 可能返回非法代理字符（surrogate），`LLMClient` 通过 `_clean_surrogates()` 自动过滤
- Windows GBK 终端无法显示 emoji，运行脚本时建议设置 `PYTHONIOENCODING=utf-8`

### 两种工具系统
- **BaseTool + ToolRegistry**: 标准系统，Agent 类通过 `to_openai_tools()` 转为 OpenAI function calling 格式
- **ToolExecutor**: 文本格式的 Action/Observation 工具执行器，被 ReActAgent 使用（基于正则解析 `ToolName[input]` 格式）
- SearchTool（BaseTool 子类）与 search.py（独立函数）功能重复，SearchTool 仍有 `os.getenv` 问题未修复

### RAG 流程
1. `FileLoader.load()` → `RecursiveCharacterSplitter.split()` → `EmbeddingClient.embed_batch()` → `VectorStore.add()`
2. 查询: `Retriever.retrieve()`（嵌入+向量搜索+可选 LLM 重排序）→ `RAGEngine.query()`

### Agent 循环
Agent 类基于 OpenAI function calling，循环：LLM 调用 → 若返回 tool_calls 则执行并追加结果 → 继续直到 LLM 返回纯文本。`ReActAgent` 类使用文本格式的 Thought/Action/Observation 循环（被 `ToolExecutor` 驱动）。
