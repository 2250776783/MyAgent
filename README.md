# myAgent

个人问答助手，具备私有知识库和行动执行能力。本项目旨在学习 **RAG** 和 **Agent** 相关知识。

## 目标

### Agent
- Agent 项目文件结构、MCP、Skills、SubAgent、Tools、WorkFlow
- 推理模式：ReAct、Plan-and-Execute、Reflection、Chain of Thought（思维链）
- 记忆机制（长短期记忆）、复杂任务拆分、Multi-agent、反思机制

### RAG
- 离线阶段：文件加载/上传 → 文档切分 → 向量数据库
- 在线阶段：Query处理 → 向量检索（粗排）→ ReRank（精排）→ 生成答案

## 环境搭建

### 前置要求
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)（包管理工具）

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd myAgent

# 安装依赖（含 dev 依赖）
uv sync --dev

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 目录结构

```
myAgent/
├── src/
│   ├── rag/          # RAG 相关代码
│   │   ├── loader/   # 文档加载
│   │   ├── splitter/ # 文档切分
│   │   ├── embed/    # 向量化
│   │   └── retriever/# 检索（含 rerank）
│   ├── agent/        # Agent 相关代码
│   │   ├── tools/    # 工具定义
│   │   ├── memory/   # 记忆机制
│   │   └── planner/  # 规划模块
│   ├── llm/          # LLM 封装层
│   └── config/       # 配置管理
├── data/             # 知识库原始文档
├── tests/            # 测试
│   ├── test_rag/
│   └── test_agent/
├── notebooks/        # 实验 notebook
├── scripts/          # 工具脚本
└── pyproject.toml    # 项目元数据和依赖
```

## 技术栈

| 组件 | 选型 |
|------|------|
| 语言 | Python 3.12 |
| 包管理 | uv |
| LLM | OpenAI API（兼容模式，可切换 Ollama） |
| 向量数据库 | ChromaDB |
| Embedding | text-embedding-3-small |
| 文档处理 | unstructured + langchain-text-splitters |
| 测试 | pytest |
| 代码质量 | ruff（lint + format）+ mypy（type check） |
