# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人问答助手项目，目标是通过实践学习 **RAG** 和 **Agent** 相关知识。

**当前状态**: 核心功能已实现。Agent Context System (`src/agent/context/`) + 记忆系统 (`src/agent/memory/`) + 企业级日志系统 (`src/logging/`) 已完成，规划模块 (`src/agent/planner/`) 仍为待实现。共 140+ 个测试。

## 技术栈

- Python 3.11+, 包管理使用 `uv`
- LLM: OpenAI API 兼容模式，生产使用 DeepSeek v4 flash
- 向量数据库: ChromaDB（持久化到 `./chroma_db`）
- 文档处理: unstructured + langchain-text-splitters
- 网页搜索: SerpApi (`google-search-results`)
- Web 框架: FastAPI + uvicorn + SSE (Server-Sent Events) + WebSocket
- 前端: Vite + React 18 + TypeScript + Tailwind CSS + Zustand
- 代码质量: ruff (lint+format) + mypy
- 持久化存储: PostgreSQL 16 + pgvector（Docker）+ Redis 7（Docker）
- 异步数据库驱动: asyncpg（连接池）+ redis.asyncio

## Docker 基础设施

```bash
# 启动 PostgreSQL + Redis
docker compose -f docker/docker-compose.yml up -d

# 检查状态
docker compose -f docker/docker-compose.yml ps

# 验证全套基础设施
uv run python scripts/verify_infra.py

# 停止
docker compose -f docker/docker-compose.yml stop

# 完全重置（删除数据卷）
docker compose -f docker/docker-compose.yml down -v
```

## 环境变量

`.env` 文件配置（pydantic-settings 自动读取，不注入 `os.environ`）:

| 变量 | 用途 |
|------|------|
| `DEEPSEEK_API_KEY` | LLM API Key（必需） |
| `DEEPSEEK_BASE_URL` | LLM API 地址（默认 `https://api.openai.com/v1`） |
| `EMBED_API_KEY` | 嵌入模型 API Key（可选，缺省复用 LLM Key） |
| `EMBED_BASE_URL` | 嵌入模型 API 地址 |
| `SERPAPI_API_KEY` | SerpApi 网页搜索 Key（可选） |
| `LOG_LEVEL` | 日志级别（默认 `INFO`） |
| `LOG_FORMAT` | 日志格式（`json` / `text`，默认 `json`） |
| `LOG_OUTPUT` | 输出目标（`console` / `file` / `both`，默认 `console`） |
| `LOG_DIR` | 日志目录（默认 `./logs`） |
| `LOG_FILE_NAME` | 日志文件名（默认 `agent.log`） |
| `PG_HOST` | PostgreSQL 主机（默认 `localhost`） |
| `PG_PORT` | PostgreSQL 端口（默认 `5432`） |
| `PG_USER` | PostgreSQL 用户（默认 `myagent`） |
| `PG_PASSWORD` | PostgreSQL 密码（默认 `myagent_secret`） |
| `PG_DATABASE` | PostgreSQL 数据库（默认 `agent_memory`） |
| `REDIS_HOST` | Redis 主机（默认 `localhost`） |
| `REDIS_PORT` | Redis 端口（默认 `6379`） |
| `REDIS_DB` | Redis 数据库编号（默认 `0`） |

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

# 运行 RAG 子模块测试
uv run pytest tests/test_rag/ -v

# 运行日志系统测试
uv run pytest tests/test_logging/ -v

# 运行日志系统测试（含覆盖率）
uv run pytest tests/test_logging/ --cov=src/logging --cov-report=term-missing -v

# 运行单测（不捕获输出，便于调试）
uv run pytest tests/test_agent/test_agent.py -v -s

# 测试覆盖率报告
uv run pytest --cov=src --cov-report=term-missing

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

# 启动 Web API 服务器
uv run python scripts/serve.py

# 指定端口和自动重载
uv run python scripts/serve.py --port 8080 --reload

# 启动 Web 服务器（text 格式 + 文件日志）
uv run python scripts/serve.py --log-format text --log-dir ./logs --log-file myagent.log

# 测试 API 健康检查
curl http://localhost:8000/api/health

# 非流式聊天
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 前端开发服务器（需先启动后端）
cd web && npm run dev

# 前端构建
cd web && npm run build
```

## 项目架构

```
src/
├── config/settings.py    # pydantic-settings 配置，自动读取 .env
├── llm/                  # LLM 调用封装
│   ├── client.py         # LLMClient: 同步/流式 chat，tool calling，重试，surrogate 清理
│   ├── async_client.py   # AsyncLLMClient: 异步 LLM 客户端（包装 AsyncOpenAI）
│   ├── types.py          # Message: role/content/tool_calls/tool_call_id/reasoning_content
│   └── tokenizer.py      # TokenCounter: tiktoken 计数
├── rag/                  # RAG 流程
│   ├── loader/loader.py  # FileLoader, DirectoryLoader, Document
│   ├── splitter/         # RecursiveCharacterSplitter
│   ├── embed/embedder.py # EmbeddingClient: OpenAI 兼容嵌入
│   ├── retriever/        # VectorStore(ChromaDB), ReRanker(LLM), Retriever(编排)
│   └── engine.py         # RAGEngine: 检索→增强→生成
├── api/                  # Web API 层（FastAPI）
│   ├── app.py            # FastAPI app factory + CORS + TTL 清理
│   ├── deps.py           # FastAPI DI（session、agent 工厂）
│   ├── models/           # Pydantic 请求/响应模型
│   ├── routers/          # API 路由（chat/health/sessions）
│   └── sessions/         # SessionStore（内存 Session 管理 + TTL）
├── agent/
│   ├── agent.py          # Agent 主类（同步 ReAct 循环）
│   ├── async_agent.py    # AsyncAgent（异步 ReAct 循环，run_in_executor 执行工具）
│   ├── ReflectionAgent.py # 实验性反思式 Agent（代码生成→自我审查→改进）
│   ├── context/          # 上下文管理系统（9 个子模块 + Manager Facade）
│   ├── tools/
│   │   ├── base/         # BaseTool 抽象基类、ToolRegistry、输出/错误类型
│   │   ├── capabilities/ # 能力域工具实现（system/code/web/rag）
│   │   ├── runtime/      # ToolExecutor 执行器 + ToolTracer 追踪
│   │   ├── policies/     # 安全检查与权限策略
│   │   └── memory/       # （空占位）
│   ├── memory/           # 分层记忆系统（10 个子模块 + Manager Facade）
│   │   └── stores/       # 存储后端：ChromaMemoryStore / SQLMemoryStore / PGVectorMemoryStore
│   └── planner/          # 待实现
scripts/
├── chat.py               # Agent 交互式对话（CLI）
├── serve.py              # Web 服务器启动入口
├── ingest.py             # RAG 数据摄入
└── query.py              # RAG 知识库查询
tests/
├── test_rag/             # RAG 子模块测试
├── test_agent/           # Agent + 工具 + 记忆测试
└── 共 12 个测试文件
web/                       # React 前端
├── package.json           # Node.js 依赖
├── vite.config.ts         # Vite 配置（含 /api 代理）
├── tailwind.config.js
├── src/
│   ├── main.tsx           # 入口
│   ├── App.tsx            # 布局（含 SessionSidebar + ChatWindow）
│   ├── api/
│   │   ├── ws.ts          # WebSocket 客户端
│   │   └── client.ts      # REST 客户端（session CRUD）
│   ├── store/chat.ts      # Zustand 状态管理
│   ├── types/chat.ts      # 类型定义
│   └── components/
│       ├── ChatWindow.tsx
│       ├── MessageList.tsx
│       ├── MessageBubble.tsx
│       ├── ToolCallCard.tsx
│       ├── InputBar.tsx
│       └── SessionSidebar.tsx
```

## 关键约定

### 配置
- 所有配置通过 `src.config.settings` 导入（pydantic-settings 自动读取 `.env`）
- `.env` 变量**不会**注入 `os.environ`，必须通过 `settings` 对象读取

### LLM 兼容性
- 默认使用 DeepSeek v4 flash（支持 thinking/reasoning 模式）
- DeepSeek API 返回 `reasoning_content` 字段，Message 类型已包含
- DeepSeek 可能返回非法代理字符（surrogate），`LLMClient._clean_surrogates()` 自动过滤
- `LLMClient.think()` 提供流式 streaming 接口（用于 ReflectionAgent 等独立场景），而 `.chat()` 为同步/非流式核心调用
- Windows GBK 终端无法显示 emoji，运行脚本建议 `PYTHONIOENCODING=utf-8`

### Web API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/chat` | 非流式聊天 |
| POST | `/api/chat/stream` | SSE 流式聊天 |
| WS | `/api/ws/chat` | WebSocket 实时聊天（流式事件） |
| GET | `/api/sessions` | 活跃 session 列表 |
| GET | `/api/sessions/{id}` | Session 详情 |
| GET | `/api/sessions/{id}/messages` | Session 消息历史 |
| DELETE | `/api/sessions/{id}` | 删除 session |

```bash
# 启动 Web 服务器
uv run python scripts/serve.py

# 非流式请求
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 流式请求（SSE）
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

### WebSocket 实时聊天协议 (`/api/ws/chat`)

WebSocket 端点接受 JSON 消息并流式返回结构化事件：

**请求格式:**
```json
{"message": "你好", "session_id": "可选"}
```

**响应事件:**
| 事件类型 | data 字段 | 说明 |
|----------|-----------|------|
| `token` | `{"text": "..."}` | 文本块 |
| `tool_call` | `{"id", "name", "args"}` | 工具调用 |
| `tool_result` | `{"name", "output"}` | 工具结果 |
| `done` | `{"session_id": "..."}` | 完成 |
| `error` | `{"message": "..."}` | 错误 |

### 前端开发

```bash
# 同时启动后端和前端（两个终端）
# 终端 1: 后端
uv run python scripts/serve.py

# 终端 2: 前端 (Vite dev server, 代理 /api → localhost:8000)
cd web && npm run dev

# 生产构建
cd web && npm run build
```

前端技术栈: Vite + React 18 + TypeScript + Tailwind CSS + Zustand

### AsyncAgent + AsyncLLMClient (`src/agent/async_agent.py`)

异步 Agent 与同步 Agent 接口一致，但使用 `async/await`：

```python
from src.llm import AsyncLLMClient
from src.agent.async_agent import AsyncAgent

llm = AsyncLLMClient()
agent = AsyncAgent(llm=llm, tools=[...])

# 异步调用
result = await agent.chat("你好")

# 异步流式
async for chunk in agent.chat_stream("你好"):
    print(chunk, end="")
```

关键差异：
- 使用 `AsyncOpenAI`（异步 HTTP 客户端），不阻塞事件循环
- 工具执行通过 `ToolExecutor` + `run_in_executor`，修复了同步 Agent 绕过执行器的问题
- ContextManager/MemoryManager 通过 `AsyncLLMClient.sync` 属性获取同步 LLM 引用

### Agent 类 (`src/agent/agent.py`)
- **Context System 集成**: Agent 自动创建 `ContextManager` 实例（`self.context`），memory 通过 context 系统间接使用
  - 也可直接传入 `context_manager=` 覆盖默认实现（优先级高于 `memory=`）
  - `on_chat_start`: 调用 `context.build_system_augmentation()` 将记忆/目标/任务/反思注入 system prompt
  - `trim_messages`: 委托给 MemoryManager 的 token 滑动窗口裁剪
  - `on_chat_end`: 触发记忆存储 + 实体提取 + 反思
- **双模式 ReAct 循环**: Function calling 优先，文本 ReAct（Thought/Action/Finish）回退
- **使用示例**:
  ```python
  from src.agent import Agent
  from src.agent.memory import MemoryManager
  
  memory = MemoryManager(llm=llm, embedder=embedder)
  agent = Agent(llm=llm, tools=[...], memory=memory)
  agent.chat("你好")
  ```

### 上下文系统 + 记忆系统生命周期
上下文系统是 Agent 的主要生命周期管理器，记忆系统作为其子系统协同工作：

```
Agent.chat()
  → ContextManager.on_chat_start()    检索记忆 → 注入 system prompt
  → ContextManager.build_system_augmentation()  构建上下文注入
  → MemoryManager.trim_messages()     窗口裁剪
  → (Agent ReAct 循环)
  → ContextManager.on_tool_call() / on_tool_result()  工具追踪
  → ContextManager.on_chat_end()      存储情景/语义/触发反思
  → Agent.reset()
  → ContextManager.on_reset()         重置
```

### 上下文系统 (`src/agent/context/`)
- **ContextManager** 是统一 Facade，Agent 在 `__init__` 中自动创建（`self.context = ContextManager(llm=llm, memory=memory)`）
- **生命周期**：`start_session()` → `on_chat_start()` / `build_system_augmentation()` → `trim_messages()` → (ReAct 循环 → `on_tool_call()` / `on_tool_result()`) → `on_chat_end()` → `on_reset()`
- **核心流程**：`build_prompt()` 内部执行：路由(Router) → 收集(各Context) → 排名(Ranker) → 压缩(Compressor) → 组装(Assembler)
- **场景感知路由**：`ContextRouter.route()` 根据 tool call 状态、错误频率、目标活跃度、溢出状态等自动选择注入哪些上下文类型
- **目标漂移检测**：`GoalContext.detect_drift()` 自动检测用户输入是否偏离当前目标，注入漂移警告
- **防 tool 输出爆炸**：`ToolContext` 追踪连续 tool call 次数，`DynamicInjector.build_anti_repetition()` 注入防重复提示
- 导入路径：
  ```python
  from src.agent.context import ContextManager, ContextType, Goal, Task
  ```

### 存储后端

| 后端 | 类型 | 用途 | 状态 |
|------|------|------|------|
| `ChromaMemoryStore` | ChromaDB（同步） | 向量存储 | 兼容保留 |
| `SQLMemoryStore` | SQLite（同步） | 结构化记忆 | 兼容保留 |
| `PGVectorMemoryStore` | PostgreSQL+pgvector（异步） | **统一存储（推荐）** | 新增 |

**PGVectorMemoryStore** 是基于 asyncpg 连接池的异步存储后端：
- CRUD: `asave` / `aget` / `asearch` / `adelete` / `aupdate` / `acount` / `aget_all`
- 辅助方法: `save_session` / `save_message` / `save_summary` / `save_tool_call`
- 使用 `<=>` 余弦距离进行向量检索，支持类型过滤：`asearch_by_type`
- 同步方法调用会抛出 `RuntimeError`，必须使用 `await` 语法
- 工具通过 Pydantic `args_schema` 声明参数，自动生成 OpenAI tool calling 格式
- 能力域驱动：`system/`, `code/`, `web/`, `rag/` 各归各类
- 所有 `_run()` 返回 `ToolOutput(success=True, output=str)` 或 `ToolOutput(success=False, error=str)`
- **分层架构**：`base/`（抽象 + 注册表）→ `capabilities/`（具体实现）→ `runtime/`（执行器 + 追踪）→ `policies/`（安全检查）
- **ToolExecutor** 提供超时控制与调用追踪（注意：同步 Agent 绕过了执行器直接调 `tool.run()`，`AsyncAgent` 已修复此问题）
- 导入路径：
  ```python
  from src.agent.tools import CalculatorTool, CurrentTimeTool, WebSearchTool
  from src.agent.tools.capabilities import RetrieverTool
  from src.agent.tools.runtime import ToolExecutor
  ```

### RAG 流程
1. 摄入: `FileLoader.load()` → `RecursiveCharacterSplitter.split()` → `EmbeddingClient.embed_batch()` → `VectorStore.add()`
2. 查询: `Retriever.retrieve()`（嵌入+向量搜索+可选 LLM 重排序）→ `RAGEngine.query()`

嵌入模型导入：
  ```python
  from src.rag.embed import EmbeddingClient  # OpenAI 兼容嵌入 API
  ```
  Embedded API Key 缺省复用 `DEEPSEEK_API_KEY`，可通过 `EMBED_API_KEY` / `EMBED_BASE_URL` 独立配置。
