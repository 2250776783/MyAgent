你是一名资深 AI Agent 基础设施工程师，请帮助我为本项目初始化一套“长期持久化记忆系统”的底层基础设施。

本项目已经有memory机制，但是使用的是chroma和mysql，以后不再使用这两个，文件 D:\project\myAgent\src\agent\memory\stores\base.py 是存储后端的统一接口，按照下面要求修改该文件

该项目后续会实现：

- 会话持久化（Conversation Persistence）
- 长期记忆（Long-term Memory）
- 向量语义检索（Vector Retrieval）
- Session 恢复
- Memory Summary 压缩
- RAG 检索
- 多 Agent 共享记忆
- Agent 状态恢复
- Tool 调用记录
- Autonomous Agent Memory

现在需要先完成基础数据库与缓存系统的部署。

请使用 Docker + Docker Compose 实现以下目标：

━━━━━━━━━━━━━━━━━━━━
【基础设施要求】
━━━━━━━━━━━━━━━━━━━━

需要部署：

1. Redis
2. PostgreSQL
3. pgvector

要求：

- 使用 Docker Compose
- PostgreSQL 使用 16 版本
- pgvector 使用官方镜像
- Redis 使用 7 版本
- 所有数据必须使用 Docker Volume 持久化
- 容器自动重启
- 使用清晰规范的容器命名
- 使用独立 Docker 网络
- 后续方便扩展

━━━━━━━━━━━━━━━━━━━━
【PostgreSQL 要求】
━━━━━━━━━━━━━━━━━━━━

PostgreSQL 用于：

- 用户数据
- Session
- Message
- Long-term Memory
- Summary
- Task
- Tool Calls
- Agent 状态

要求：

- 自动初始化 pgvector 扩展
- 自动创建 agent_memory 数据库
- 提供初始化 SQL 脚本
- 为后续数据库表预留结构

后续会创建如下表：

- users
- sessions
- messages
- conversation_summary
- long_term_memory
- tasks
- tool_calls
- memory_links

━━━━━━━━━━━━━━━━━━━━
【Redis 要求】
━━━━━━━━━━━━━━━━━━━━

Redis 用于：

- 最近会话缓存
- Agent 状态缓存
- 热记忆
- 分布式锁
- Task Queue
- Tool Cache

要求：

- 开启 AOF 持久化
- 提供 redis.conf
- 配置适合 AI Agent 场景

━━━━━━━━━━━━━━━━━━━━
【需要生成的内容】
━━━━━━━━━━━━━━━━━━━━

请生成：

1. 完整 docker-compose.yml
2. PostgreSQL 初始化脚本
3. Redis 配置文件
4. 项目目录结构
5. Docker 启动命令
6. Docker 检查命令
7. PostgreSQL 测试命令
8. pgvector 验证命令
9. Redis 验证命令
10. .env 示例
11. 健康检查（healthcheck）
12. 数据持久化配置
13. 数据库连接示例
14. 最佳实践建议

━━━━━━━━━━━━━━━━━━━━
【工程要求】
━━━━━━━━━━━━━━━━━━━━

要求：

- 使用规范工程结构
- 添加详细注释
- 方便后续扩展
- 面向 AI Agent Memory 架构设计
- 后续兼容：
  - FastAPI
  - SpringBoot
  - LangGraph
  - OpenAI SDK
  - Ollama
  - vLLM

━━━━━━━━━━━━━━━━━━━━
【重要要求】
━━━━━━━━━━━━━━━━━━━━

这是一个 AI Agent Memory 系统的底层基础设施。

后续系统会实现：

- Persistent Memory
- Semantic Retrieval
- Vector Search
- Context Compression
- Memory Ranking
- Reflection Memory
- Multi-Agent Shared Memory

因此：

数据库与缓存架构必须具备长期扩展性。

请按照“生产级 AI Agent 基础设施”的标准生成完整方案。