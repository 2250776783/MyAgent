你需要为一个 RAG + Agent 学习项目搭建 Python 开发环境，项目位于 D:\project\myAgent。

  ## 技术选型
  - 语言: Python 3.11+
  - 包管理: uv（推荐，速度更快）
  - LLM: OpenAI API（兼容模式，后续可切换到本地 Ollama）
  - 向量数据库: ChromaDB（本地轻量，适合学习）
  - Embedding: text-embedding-3-small（OpenAI）
  - 文档处理: unstructured + langchain-text-splitters
  - 测试: pytest
  - 代码质量: ruff（lint + format）+ mypy（类型检查）

  ## 要求

  ### 1. 初始化项目结构
  创建以下目录结构：
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
  └── scripts/          # 工具脚本

  ### 2. 配置管理
  - 使用 pydantic-settings 或 python-dotenv 管理配置
  - 支持 .env 文件存放 API Key 等敏感信息
  - 配置项包括：LLM_API_KEY、LLM_BASE_URL、EMBED_MODEL、CHROMA_PATH 等

  ### 3. 依赖管理
  - 用 pyproject.toml 管理项目元数据和依赖
  - 区分 dev 依赖（pytest, ruff, mypy）
  - 提供 lock 文件确保可复现

  ### 4. 开发工具配置
  - ruff 配置文件（行长度 100、推荐规则集）
  - mypy 配置文件（宽松模式起步）
  - pytest 配置（支持 src 路径导入）
  - .gitignore（包含 .env, __pycache__, chroma 数据目录等）
  - .env.example（模板文件，不含真实密钥）

  ### 5. 最小可用验证
  环境搭建完成后，写一个最小脚本验证：
  - 能成功调用 LLM API（一条简单 chat completion）
  - 能成功创建 ChromaDB 集合并写入/检索一条向量
  - 能成功用 unstructured 加载一个文本文件

  ### 6. 项目 README
  确保 README.md 更新，包含：
  - 项目简介
  - 环境搭建步骤（clone → 安装依赖 → .env 配置 → 运行验证脚本）
  - 目录结构说明

在创建系统结构的时候不要实现具体代码，我会在后续按照模块实现。