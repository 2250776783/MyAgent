你现在是一名资深前端架构师。

请帮我构建一个现代化 AI Agent 平台的前端工程。

技术栈要求：

- Next.js（App Router）
- TypeScript
- Tailwind CSS
- shadcn/ui
- Zustand（状态管理）
- React Query/TanStack Query（接口缓存）
- Axios（接口请求）
- React Hook Form + Zod（表单校验）
- Framer Motion（动画）
- Lucide React（图标）
- 支持暗黑模式
- 响应式布局
- 页面风格参考：
  - ChatGPT
  - Claude
  - Dify
  - OpenWebUI
  - Cursor
  - Vercel AI Dashboard

项目要求：

- UI 美观现代
- 工程结构清晰
- 组件高度复用
- 具备企业级后台管理风格
- 适合后续扩展 Agent / Workflow / RAG / Tool Calling
- 所有模块使用 mock API 先联调
- 所有接口统一封装
- 支持 JWT 登录鉴权
- 支持 RBAC 权限控制
- 前后端完全分离

-----------------------------------
一、用户角色设计
-----------------------------------

系统包含两类角色：

1. 普通用户（USER）
2. 管理员（ADMIN）

不同角色登录后进入不同权限界面。

管理员拥有全部权限。

普通用户只能访问自己的 Agent、聊天等资源。

-----------------------------------
二、登录认证模块
-----------------------------------

功能：

1. 登录
2. 注册
3. 退出登录
4. JWT Token 存储
5. Token 自动刷新
6. 路由权限守卫
7. 记住登录状态
8. 用户信息获取
9. 修改密码
10. 忘记密码（预留）

页面：

- /login
- /register
- /forgot-password

接口设计：

POST   /api/auth/login
POST   /api/auth/register
POST   /api/auth/logout
POST   /api/auth/refresh
GET    /api/auth/profile
PUT    /api/auth/password

登录返回：

{
  access_token,
  refresh_token,
  user_info: {
    id,
    username,
    email,
    avatar,
    role
  }
}

要求：

- Axios 请求拦截器
- 自动携带 token
- token 过期自动刷新
- 未登录自动跳转 login
- 权限不足跳转 403 页面

-----------------------------------
三、整体页面布局
-----------------------------------

系统采用：

1. 左侧 Sidebar
2. 顶部 Header
3. 中间 Main Content
4. 支持移动端折叠 Sidebar

Sidebar 模块：

- Dashboard
- Agent
- Chat
- Workflow
- Knowledge Base
- Memory
- Tools
- Logs
- Settings
- Admin（管理员可见）

要求：

- 动态菜单
- 权限菜单控制
- 面包屑导航
- 页面切换动画
- 全局 Loading
- Skeleton Loading

-----------------------------------
四、Dashboard 首页
-----------------------------------

页面路径：

/dashboard

功能：

1. 用户信息展示
2. Agent 数量统计
3. 今日消息统计
4. Token 消耗统计
5. 最近会话
6. 最近 Agent
7. 系统运行状态
8. 快速创建 Agent

接口：

GET /api/dashboard/overview
GET /api/dashboard/recent-chats
GET /api/dashboard/recent-agents

UI要求：

- 卡片式设计
- 图表统计
- 动态数据动画
- 支持暗黑模式

-----------------------------------
五、Agent 管理模块
-----------------------------------

页面路径：

/agents

功能：

1. Agent 列表
2. 创建 Agent
3. 编辑 Agent
4. 删除 Agent
5. Agent 配置
6. Agent Prompt 编辑
7. 模型参数配置
8. Tool 绑定
9. Memory 绑定
10. 知识库绑定

接口：

GET    /api/agents
POST   /api/agents
GET    /api/agents/:id
PUT    /api/agents/:id
DELETE /api/agents/:id

Agent 数据结构：

{
  id,
  name,
  description,
  avatar,
  model,
  temperature,
  system_prompt,
  tools,
  memory_enabled,
  knowledge_base_ids,
  created_at
}

要求：

- 支持分页
- 搜索
- 筛选
- 卡片视图
- 表格视图
- Agent Avatar

-----------------------------------
六、聊天模块（核心）
-----------------------------------

页面路径：

/chat

功能：

1. ChatGPT 风格聊天界面
2. 流式输出
3. Markdown 渲染
4. Code Highlight
5. 文件上传
6. 多轮对话
7. 会话历史
8. 会话删除
9. Tool 调用展示
10. Thinking 状态展示
11. Token 使用展示
12. 中断生成
13. 重新生成
14. 多 Agent 对话（后续预留）

接口：

GET    /api/chat/sessions
POST   /api/chat/session
GET    /api/chat/session/:id
DELETE /api/chat/session/:id

POST   /api/chat/completions

消息结构：

{
  role,
  content,
  timestamp,
  tool_calls,
  token_usage
}

要求：

- 支持 SSE/流式响应
- 自动滚动
- Chat 输入框固定底部
- 支持 Enter 发送
- Shift + Enter 换行
- 美观的 AI 消息气泡
- Tool 调用状态可视化

-----------------------------------
七、Workflow 工作流模块
-----------------------------------

页面路径：

/workflow

功能：

1. 节点编排
2. 拖拽节点
3. Tool 节点
4. Agent 节点
5. 条件节点
6. 开始/结束节点
7. 节点连线
8. Workflow 保存
9. Workflow 执行

推荐：

- 使用 React Flow

接口：

GET    /api/workflows
POST   /api/workflows
PUT    /api/workflows/:id
DELETE /api/workflows/:id
POST   /api/workflows/:id/run

要求：

- 类似 Dify / LangFlow 风格
- 支持缩放
- 小地图
- 节点属性面板

-----------------------------------
八、Knowledge Base 知识库模块
-----------------------------------

页面路径：

/knowledge

功能：

1. 上传文件
2. 文件管理
3. 文档切片展示
4. 向量化状态
5. 检索测试
6. 文档删除

接口：

GET    /api/knowledge/files
POST   /api/knowledge/upload
DELETE /api/knowledge/files/:id
POST   /api/knowledge/search

要求：

- 拖拽上传
- 文件类型图标
- 上传进度
- 状态标签

-----------------------------------
九、Memory 记忆模块
-----------------------------------

页面路径：

/memory

功能：

1. 长期记忆查看
2. Session Memory
3. Memory 搜索
4. Memory 删除
5. Memory 标签
6. Memory 时间线

接口：

GET    /api/memory
DELETE /api/memory/:id
POST   /api/memory/search

要求：

- 时间线 UI
- 标签分类
- 记忆详情 Drawer

-----------------------------------
十、Tool 管理模块
-----------------------------------

页面路径：

/tools

功能：

1. Tool 列表
2. Tool 配置
3. Tool 启用/禁用
4. API Key 配置
5. Tool 测试

接口：

GET    /api/tools
PUT    /api/tools/:id

-----------------------------------
十一、日志监控模块
-----------------------------------

页面路径：

/logs

功能：

1. Agent 执行日志
2. Tool 调用日志
3. 错误日志
4. Token 消耗日志

接口：

GET /api/logs

要求：

- 实时日志滚动
- 日志等级颜色区分
- 支持搜索过滤

-----------------------------------
十二、管理员模块
-----------------------------------

页面路径：

/admin

仅管理员可访问。

功能：

1. 用户管理
2. 用户封禁
3. 系统配置
4. 模型配置
5. API Key 管理
6. 系统监控
7. 公告管理

接口：

GET    /api/admin/users
PUT    /api/admin/users/:id
DELETE /api/admin/users/:id

GET    /api/admin/system

-----------------------------------
十三、前端工程结构要求
-----------------------------------

请设计完整工程结构：

src/
  app/
  components/
  features/
  hooks/
  services/
  store/
  lib/
  types/
  utils/
  layouts/

要求：

1. 模块化架构
2. 组件拆分合理
3. hooks 抽离
4. API 单独管理
5. 类型统一管理
6. 权限统一管理
7. 错误边界
8. 全局 Toast
9. Loading 管理
10. 环境变量管理

-----------------------------------
十四、需要生成的内容
-----------------------------------

请直接生成：

1. 完整项目目录结构
2. 所有核心页面
3. Sidebar Layout
4. 登录鉴权逻辑
5. Axios 封装
6. Zustand Store
7. React Query 配置
8. mock API
9. 所有基础组件
10. 示例页面
11. 页面路由
12. 类型定义
13. 权限控制
14. 暗黑模式
15. README
16. 启动方式

要求：

- 代码完整
- 可直接运行
- 工程规范
- 注释清晰
- UI 现代化
- 不允许只生成伪代码