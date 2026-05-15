# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人问答助手项目，目标是通过实践学习 **RAG** 和 **Agent** 相关知识。

**当前状态**: 核心功能已实现。Agent 记忆系统 (`src/agent/memory/`) 和规划模块 (`src/agent/planner/`) 仍为空骨架。

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
uv run pytest tests/test_agent/test_agent.py -v

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

## 项目架构

```
src/
├── config/settings.py    # pydantic-settings 配置，自动读取 .env
├── llm/                  # LLM 调用封装
│   ├── client.py         # LLMClient: 同步/流式 chat，tool calling，重试，surrogate 清理
│   ├── types.py          # Message: role/content/tool_calls/tool_call_id/reasoning_content
│   └── tokenizer.py      # TokenCounter: tiktoken 计数
├── rag/                  # RAG 流程
│   ├── loader/loader.py  # FileLoader, DirectoryLoader, Document
│   ├── splitter/         # RecursiveCharacterSplitter
│   ├── embed/embedder.py # EmbeddingClient: OpenAI 兼容嵌入
│   ├── retriever/        # VectorStore(ChromaDB), ReRanker(LLM), Retriever(编排)
│   └── engine.py         # RAGEngine: 检索→增强→生成
├── agent/
│   ├── agent.py          # Agent 主类（统一的 ReAct 循环，双模式：function calling + 文本 ReAct）
│   ├── tools/            # 能力域驱动的工具系统
│   │   ├── base/         # BaseTool 抽象基类 + ToolRegistry + ToolOutput + 参数 schema + 错误体系
│   │   ├── capabilities/ # 按能力域组织的工具集
│   │   │   ├── system/   # CurrentTimeTool
│   │   │   ├── code/     # CalculatorTool
│   │   │   ├── web/      # WebSearchTool（SerpApi）
│   │   │   └── rag/      # RetrieverTool（RAG 知识库检索）
│   │   ├── runtime/      # ToolExecutor（超时、重试、追踪）+ ToolTracer
│   │   └── policies/     # 安全策略（权限校验）
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

### LLM 兼容性
- 默认使用 DeepSeek v4 flash（支持 thinking/reasoning 模式）
- DeepSeek API 返回 `reasoning_content` 字段，Message 类型已包含该字段
- DeepSeek 可能返回非法代理字符（surrogate），`LLMClient` 通过 `_clean_surrogates()` 自动过滤
- Windows GBK 终端无法显示 emoji，运行脚本时建议设置 `PYTHONIOENCODING=utf-8`

### Agent 双模式 ReAct 循环
Agent 类同时支持两种模式：
1. **Function calling 模式**（默认优先）：LLM 返回 `tool_calls` 时执行对应工具
2. **文本 ReAct 模式**（回退）：LLM 返回 `Thought:`/`Action:` 格式时通过正则解析并执行工具，`Action: Finish[答案]` 直接结束循环

### 工具系统结构（能力域驱动）
- `base/`: 核心抽象 — `BaseTool`（ABC）、`ToolRegistry`、`ToolOutput`、`BaseToolArgs`（Pydantic 参数 schema）
- `capabilities/`: 按能力域分类的工具实现，每个工具独立文件
- `runtime/`: `ToolExecutor` 包装 BaseTool 提供超时/重试/追踪，`execute_tool_call()` 兼容旧接口
- `policies/`: 基于 `ToolMetadata` 的权限校验（admin/standard/restricted 三级）
- 工具参数通过 Pydantic `args_schema` 声明，自动生成 OpenAI tool calling 格式

### 工具导入路径
```python
from src.agent.tools import CalculatorTool, CurrentTimeTool, WebSearchTool
from src.agent.tools.base import BaseTool, ToolRegistry, ToolOutput, BaseToolArgs, Field
from src.agent.tools.capabilities import RetrieverTool
from src.agent.tools.runtime import ToolExecutor
```

### RAG 流程
1. 摄入: `FileLoader.load()` → `RecursiveCharacterSplitter.split()` → `EmbeddingClient.embed_batch()` → `VectorStore.add()`
2. 查询: `Retriever.retrieve()`（嵌入+向量搜索+可选 LLM 重排序）→ `RAGEngine.query()`
