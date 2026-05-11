# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人问答助手项目，目标是通过实践学习 **RAG** 和 **Agent** 相关知识。项目已完成脚手架搭建，核心逻辑待实现。

## 技术栈

- Python 3.11+, 包管理使用 `uv`
- LLM: OpenAI API 兼容模式（可通过 LLM_BASE_URL 切换 Ollama）
- 向量数据库: ChromaDB
- 文档处理: unstructured + langchain-text-splitters
- 代码质量: ruff (lint+format) + mypy

## 开发命令

```bash
# 安装依赖（含 dev）
uv sync --dev

# 运行所有测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/test_rag/test_something.py

# Lint 检查
uv run ruff check src/

# 自动格式化
uv run ruff format src/

# 类型检查
uv run mypy src/

# 运行特定模块（示例）
uv run python -m src.rag.loader
```

## 项目架构

```
src/
├── config/        # 配置管理（pydantic-settings，已实现）
├── llm/           # LLM 调用封装层（待实现）
├── rag/           # RAG 流程
│   ├── loader/    # 文档加载（支持 unstructured）
│   ├── splitter/  # 文档切分
│   ├── embed/     # 向量化（OpenAI embedding）
│   └── retriever/ # 向量检索 + ReRank
├── agent/         # Agent 逻辑
│   ├── tools/     # 工具定义
│   ├── memory/    # 记忆机制（长短期记忆）
│   └── planner/   # 规划模块（ReAct, Plan-and-Execute 等）
tests/
├── test_rag/
└── test_agent/
data/              # 知识库原始文档
notebooks/         # 实验 notebook
scripts/           # 工具脚本
```

## 关键约定

- 配置统一通过 `src.config.settings` 导入（基于 pydantic-settings，自动读取 `.env`）
- 行长度 100，引号风格双引号（ruff 已配置）
- 当前所有模块均为空骨架，按需逐个实现
- ChromaDB 数据持久化到 `./chroma_db`（已加入 .gitignore）
