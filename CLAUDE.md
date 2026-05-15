# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人问答助手项目，目标是通过实践学习 **RAG** 和 **Agent** 相关知识。

**当前状态**: 核心功能已实现。Agent 记忆系统 (`src/agent/memory/`) 已完成，规划模块 (`src/agent/planner/`) 仍为待实现。共 115 个测试。

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

# 运行记忆系统测试
uv run pytest tests/test_agent/test_memory.py -v

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
│   ├── agent.py          # Agent 主类（统一 ReAct 循环，双模式 + 可选记忆系统）
│   ├── tools/            # 能力域驱动的工具系统
│   │   ├── base/         # BaseTool + ToolRegistry + ToolOutput + 参数 schema
│   │   ├── capabilities/ # 按能力域组织的工具集
│   │   │   ├── system/   # CurrentTimeTool
│   │   │   ├── code/     # CalculatorTool
│   │   │   ├── web/      # WebSearchTool（SerpApi）
│   │   │   └── rag/      # RetrieverTool（RAG 知识库检索）
│   │   ├── runtime/      # ToolExecutor（超时、重试、追踪）
│   │   └── policies/     # 安全策略（权限校验）
│   ├── memory/            # 分层记忆系统
│   │   ├── manager.py    # MemoryManager Facade
│   │   ├── working.py    # WorkingMemory（token 滑动窗口裁剪）
│   │   ├── episodic.py   # EpisodicMemory（会话摘要 + 关键事件）
│   │   ├── semantic.py   # SemanticMemory（实体/偏好提取与合并）
│   │   ├── retrieval.py  # MemoryRetriever（查询扩展 + 多层检索 + 加权排序）
│   │   ├── reflection.py # ReflectionSystem（定期反思提取洞察）
│   │   ├── decay.py      # ForgettingMechanism（分层遗忘衰减）
│   │   ├── injector.py   # PromptInjector（记忆注入到 system prompt）
│   │   ├── scorer.py     # ImportanceScorer（多维度重要性评分）
│   │   ├── summarizer.py # MemorySummarizer（LLM 摘要压缩）
│   │   ├── resolver.py   # ConflictResolver（实体矛盾检测与统一）
│   │   ├── router.py     # MemoryRouter（读写路由）
│   │   ├── types.py      # 数据模型
│   │   └── stores/       # 双存储后端
│   │       ├── chroma_store.py  # ChromaDB 向量存储
│   │       └── sql_store.py     # SQLite 结构化存储
│   └── planner/          # 待实现
scripts/
├── chat.py               # Agent 交互式对话
├── ingest.py             # RAG 数据摄入
└── query.py              # RAG 知识库查询
tests/
├── test_rag/             # RAG 子模块测试
└── test_agent/           # Agent + 工具 + 记忆测试
```

## 关键约定

### 配置
- 所有配置通过 `src.config.settings` 导入（pydantic-settings 自动读取 `.env`）
- `.env` 变量**不会**注入 `os.environ`，必须通过 `settings` 对象读取

### LLM 兼容性
- 默认使用 DeepSeek v4 flash（支持 thinking/reasoning 模式）
- DeepSeek API 返回 `reasoning_content` 字段，Message 类型已包含
- DeepSeek 可能返回非法代理字符（surrogate），`LLMClient._clean_surrogates()` 自动过滤
- Windows GBK 终端无法显示 emoji，运行脚本建议 `PYTHONIOENCODING=utf-8`

### Agent 类 (`src/agent/agent.py`)
- **可选记忆系统**: 传入 `memory=MemoryManager(...)` 自动启用记忆生命周期
  - `on_chat_start`: 检索相关记忆注入 system prompt
  - `trim_messages`: token 滑动窗口裁剪
  - `on_chat_end`: 存储情景记忆 + 提取实体/偏好 + 触发反思
- **双模式 ReAct 循环**: Function calling 优先，文本 ReAct（Thought/Action/Finish）回退
- **使用示例**:
  ```python
  from src.agent import Agent
  from src.agent.memory import MemoryManager
  memory = MemoryManager(llm=llm, embedder=embedder)
  agent = Agent(llm=llm, tools=[...], memory=memory)
  agent.chat("你好")
  ```

### 记忆系统生命周期
```
start_session()
  → on_chat_start(user_input)  检索记忆 → 注入 system prompt
  → trim_messages(messages)    窗口裁剪
  → (Agent ReAct 循环)
  → on_chat_end(messages)      存储情景/语义/触发反思
  → on_reset()                 重置
```

### 工具系统
- 工具通过 Pydantic `args_schema` 声明参数，自动生成 OpenAI tool calling 格式
- 能力域驱动：`system/`, `code/`, `web/`, `rag/` 各归各类
- 导入路径：
  ```python
  from src.agent.tools import CalculatorTool, CurrentTimeTool, WebSearchTool
  from src.agent.tools.capabilities import RetrieverTool
  from src.agent.tools.runtime import ToolExecutor
  ```

### RAG 流程
1. 摄入: `FileLoader.load()` → `RecursiveCharacterSplitter.split()` → `EmbeddingClient.embed_batch()` → `VectorStore.add()`
2. 查询: `Retriever.retrieve()`（嵌入+向量搜索+可选 LLM 重排序）→ `RAGEngine.query()`
