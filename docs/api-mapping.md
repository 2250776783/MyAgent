# API 接口联调文档

> **正式 OpenAPI 3.0 规范** 见 [`openapi.yaml`](./openapi.yaml)（44 个 Schema / 33 个端点）。  
> 端服务运行时也可通过 `GET /api/openapi.yaml` 获取。

## 概述

前端 Next.js 14 通过 `next.config.js` 将 `/api/*` 代理到后端 `http://localhost:8000/api/*`。  
目前后端仅实现了 `health/chat/sessions/ws` 四个路由，其余需新增。

---

## 已实现接口（后端已有，可联调）

| 方法 | 路径 | 前端调用 | 备注 |
|------|------|---------|------|
| GET | `/api/health` | 未调用 | 健康检查 |
| POST | `/api/chat` | `POST /api/chat/completions` ❌路径不一致 | 非流式聊天 |
| POST | `/api/chat/stream` | 未调用 | SSE 流式聊天 |
| WS | `/api/ws/chat` | 前端 ws.ts 连接此端点 ✅ | WebSocket 实时聊天 |
| GET | `/api/sessions` | 前端调 `GET /chat/sessions` ❌路径不一致 | 会话列表 |
| GET | `/api/sessions/{id}` | 前端调 `GET /chat/sessions/{id}` ❌路径不一致 | 会话详情 |
| GET | `/api/sessions/{id}/messages` | 前端未独立调用 | 会话消息 |
| DELETE | `/api/sessions/{id}` | 前端调 `DELETE /chat/sessions/{id}` ❌路径不一致 | 删除会话 |

---

## 未实现接口（需要后端新增）

### 1. 认证 `/api/auth/*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| POST | `/api/auth/login` | `api/auth.ts` | 登录，返回 `{access_token, refresh_token, user}` |
| POST | `/api/auth/register` | `api/auth.ts` | 注册 |
| POST | `/api/auth/logout` | `api/auth.ts` | 登出 |
| POST | `/api/auth/refresh` | `api/client.ts` 拦截器 | Token 刷新 |
| GET | `/api/auth/profile` | `api/auth.ts` | 当前用户信息 |
| PUT | `/api/auth/password` | `api/auth.ts` | 修改密码 |

**当前状态**: 前端 `stores/auth-store.ts` 有硬编码 mock，不调后端。联调时需移除 mock 改为调真实接口。

**Token 数据流**: 前端期望 `access_token`(JWT) 和 `refresh_token`，store 存到 localStorage 并同步 cookie 供 middleware 校验。

---

### 2. Agent 管理 `/api/agents*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/agents` | `api/agents.ts` | 列表，支持 `?page=&search=` |
| GET | `/agents/{id}` | `api/agents.ts` | 详情 |
| POST | `/agents` | `api/agents.ts` | 创建 |
| PUT | `/agents/{id}` | `api/agents.ts` | 更新 |
| DELETE | `/agents/{id}` | `api/agents.ts` | 删除 |

**数据类型**: `Agent` 包含 `{id, name, description, model, provider, temperature, max_tokens, top_p, system_prompt, tools[], memory_enabled, knowledge_base_ids[], status, created_at, updated_at, user_id}`

---

### 3. 知识库 `/api/knowledge/*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/knowledge/files` | `api/knowledge.ts` | 文档列表，返回 `{success, data: KnowledgeDocument[]}` |
| POST | `/knowledge/upload` | `api/knowledge.ts` | 上传文件（multipart/form-data）|
| DELETE | `/knowledge/files/{id}` | `api/knowledge.ts` | 删除文档 |
| POST | `/knowledge/search` | `api/knowledge.ts` | 语义搜索，body `{query, limit?}` |

**数据类型**: `KnowledgeDocument {id, filename, file_type, file_size, chunk_count, status, created_at}`, `SearchResult {id, content, score, document_id}`

---

### 4. 记忆 `/api/memory*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/memory` | `api/memory.ts` | 列表，支持 `?page=` |
| POST | `/memory/search` | `api/memory.ts` | 语义搜索，body `{query, limit?}` |
| DELETE | `/memory/{id}` | `api/memory.ts` | 删除记忆 |

**数据类型**: `Memory {id, type, content, tags[], importance_score, confidence_score, created_at}`

---

### 5. 工作流 `/api/workflows*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/workflows` | `api/workflow.ts` | 列表 |
| GET | `/workflows/{id}` | `api/workflow.ts` | 详情 |
| POST | `/workflows` | `api/workflow.ts` | 创建 |
| PUT | `/workflows/{id}` | `api/workflow.ts` | 更新 |
| DELETE | `/workflows/{id}` | `api/workflow.ts` | 删除 |

**注意**: 前端 workflow editor 保存时发送的 `nodes` 是 React Flow 格式 `{id, type, position, data}`，`edges` 是 `{id, source, target, sourceHandle?, targetHandle?, animated?}`。

---

### 6. 工具 `/api/tools*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/tools` | `api/tools.ts` | 列表 |
| PUT | `/tools/{id}` | `api/tools.ts` | 更新（启/禁用开关） |

**数据类型**: `Tool {id, name, description, icon, category, enabled, config}`

---

### 7. 日志 `/api/logs*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/logs` | `api/logs.ts` | 列表，支持 `?level=&search=&source=&page=&limit=` |

**数据类型**: `LogEntry {id, timestamp, level, message, source, trace_id?, details?}`

---

### 8. 管理后台 `/api/admin*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/admin/users` | `api/admin.ts` | 用户列表 |
| PUT | `/admin/users/{id}` | `api/admin.ts` | 更新用户（角色/状态）|
| DELETE | `/admin/users/{id}` | `api/admin.ts` | 删除用户 |
| GET | `/admin/system` | `api/admin.ts` | 系统指标 |
| PUT | `/admin/system` | `api/admin.ts` | 更新系统配置 |

**数据类型**: `SystemMetrics {total_users, active_sessions, total_agents, total_messages, api_calls_today, tokens_used_today, system_uptime, cpu_usage, memory_usage}`

---

### 9. 设置 `/api/settings*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/settings` | `api/settings.ts` | 获取设置 |
| PUT | `/settings` | `api/settings.ts` | 更新设置 |

---

### 10. 仪表盘 `/api/dashboard/*`

| 方法 | 路径 | 前端文件 | 说明 |
|------|------|---------|------|
| GET | `/dashboard/overview` | `api/dashboard.ts` | 总览数据（消息数/会话数/Agent数/响应时间）|
| GET | `/dashboard/recent-chats` | `api/dashboard.ts` | 最近聊天 |
| GET | `/dashboard/recent-agents` | `api/dashboard.ts` | 最近 Agent |

---

## 前后端路径不一致问题

以下接口存在路由前缀差异，联调前需对齐：

| 前端调用 | 后端实际路径 | 建议方案 |
|---------|-------------|---------|
| `POST /api/chat/completions` | `POST /api/chat` | 前端改为调 `/api/chat` |
| `GET /chat/sessions` | `GET /api/sessions` | 前端改为 `/api/sessions` |
| `GET /chat/sessions/{id}` | `GET /api/sessions/{id}` | 前端改为 `/api/sessions/{id}` |
| `POST /chat/session` | 不存在 | 后端新增 |
| `DELETE /chat/sessions/{id}` | `DELETE /api/sessions/{id}` | 前端改为 `/api/sessions/{id}` |

---

## 通用响应格式

所有后端响应建议统一为前端 `client.ts` 期望的格式：

```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  meta?: { total: number; page: number; limit: number };
}
```

错误时 HTTP 状态码:
- `401` → 前端拦截器自动尝试 refresh token
- `403` → 无权限
- `404` → 资源不存在
- `422` → 参数校验失败
- `500` → 服务器错误

---

## 联调优先级建议

| 优先级 | 模块 | 理由 |
|--------|------|------|
| P0 | Auth | 登录是入口，目前是 mock，必须优先对接 |
| P0 | Chat + Sessions | 核心功能，后端已有基础，只需对齐路径 |
| P1 | Agents | Agent 管理是平台核心 |
| P1 | Knowledge | 依赖 Agent 的知识库能力 |
| P2 | Workflow | 编辑器已就绪，但需要运行/存储支持 |
| P2 | Logs | 需要日志系统输出 |
| P3 | Tools | 相对独立，影响小 |
| P3 | Admin/Settings/Dashboard | 管理功能，最后对接 |
