"use client";

import { Bot, MessageSquare, Code, BookOpen, Sparkles } from "lucide-react";

interface QuickAction {
  icon: React.ReactNode;
  title: string;
  description: string;
  prompt: string;
}

const quickActions: QuickAction[] = [
  {
    icon: <Code className="h-5 w-5" />,
    title: "编写代码",
    description: "生成或调试代码",
    prompt: "请帮我编写一个 Python 函数，实现...",
  },
  {
    icon: <BookOpen className="h-5 w-5" />,
    title: "知识问答",
    description: "解答技术问题",
    prompt: "请解释一下什么是 RAG（检索增强生成）？",
  },
  {
    icon: <MessageSquare className="h-5 w-5" />,
    title: "文本处理",
    description: "总结、翻译、改写",
    prompt: "请帮我总结以下内容：",
  },
  {
    icon: <Sparkles className="h-5 w-5" />,
    title: "头脑风暴",
    description: "创意和想法",
    prompt: "我们来一次头脑风暴，主题是：",
  },
];

interface Props {
  onSend: (prompt: string) => void;
}

export function WelcomeScreen({ onSend }: Props) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 p-8">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <Bot className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight">MyAgent AI 助手</h1>
        <p className="max-w-md text-sm text-muted-foreground">
          我是你的 AI 智能助手，可以帮助你编写代码、回答问题、处理文本等。有什么我可以帮你的吗？
        </p>
      </div>
      <div className="grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
        {quickActions.map((action) => (
          <button
            key={action.title}
            onClick={() => onSend(action.prompt)}
            className="flex items-start gap-3 rounded-xl border p-4 text-left transition-colors hover:bg-accent hover:border-accent-foreground/20"
          >
            <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              {action.icon}
            </div>
            <div>
              <div className="text-sm font-medium">{action.title}</div>
              <div className="text-xs text-muted-foreground">{action.description}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
