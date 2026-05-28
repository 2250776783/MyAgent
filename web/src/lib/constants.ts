export const ROUTES = {
  LOGIN: "/login",
  REGISTER: "/register",
  FORGOT_PASSWORD: "/forgot-password",
  DASHBOARD: "/dashboard",
  AGENTS: "/agents",
  CHAT: "/chat",
  WORKFLOW: "/workflow",
  KNOWLEDGE: "/knowledge",
  MEMORY: "/memory",
  TOOLS: "/tools",
  LOGS: "/logs",
  SETTINGS: "/settings",
  ADMIN: "/admin",
} as const;

export const ROLES = {
  USER: "USER",
  ADMIN: "ADMIN",
} as const;

export const SIDEBAR_ITEMS = [
  { label: "仪表盘", href: ROUTES.DASHBOARD, icon: "LayoutDashboard", roles: ["USER", "ADMIN"] },
  { label: "Agent", href: ROUTES.AGENTS, icon: "Bot", roles: ["USER", "ADMIN"] },
  { label: "聊天", href: ROUTES.CHAT, icon: "MessageSquare", roles: ["USER", "ADMIN"] },
  { label: "工作流", href: ROUTES.WORKFLOW, icon: "Workflow", roles: ["USER", "ADMIN"] },
  { label: "知识库", href: ROUTES.KNOWLEDGE, icon: "Library", roles: ["USER", "ADMIN"] },
  { label: "记忆", href: ROUTES.MEMORY, icon: "Brain", roles: ["USER", "ADMIN"] },
  { label: "工具", href: ROUTES.TOOLS, icon: "Wrench", roles: ["USER", "ADMIN"] },
  { label: "日志", href: ROUTES.LOGS, icon: "ScrollText", roles: ["USER", "ADMIN"] },
  { label: "设置", href: ROUTES.SETTINGS, icon: "Settings", roles: ["USER", "ADMIN"] },
  { label: "管理", href: ROUTES.ADMIN, icon: "Shield", roles: ["ADMIN"] },
] as const;

export const API_PATHS = {
  AUTH: {
    LOGIN: "/auth/login",
    REGISTER: "/auth/register",
    LOGOUT: "/auth/logout",
    REFRESH: "/auth/refresh",
    PROFILE: "/auth/profile",
    PASSWORD: "/auth/password",
  },
  AGENTS: "/agents",
  SESSIONS: "/chat/sessions",
  CHAT: "/chat/completions",
  WORKFLOWS: "/workflows",
  KNOWLEDGE: {
    FILES: "/knowledge/files",
    UPLOAD: "/knowledge/upload",
    SEARCH: "/knowledge/search",
  },
  MEMORY: "/memory",
  TOOLS: "/tools",
  LOGS: "/logs",
  ADMIN: {
    USERS: "/admin/users",
    SYSTEM: "/admin/system",
  },
  DASHBOARD: {
    OVERVIEW: "/dashboard/overview",
    RECENT_CHATS: "/dashboard/recent-chats",
    RECENT_AGENTS: "/dashboard/recent-agents",
  },
  SETTINGS: "/settings",
} as const;

export const TOKEN_KEY = "access_token";
export const REFRESH_TOKEN_KEY = "refresh_token";
