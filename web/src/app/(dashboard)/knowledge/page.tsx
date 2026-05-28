"use client";

import { useState, useEffect } from "react";
import { Search, FileText, Trash2 } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { FileUpload } from "@/components/knowledge/file-upload";
import { knowledgeApi } from "@/api/knowledge";
import { formatRelativeTime } from "@/lib/utils";
import type { KnowledgeDocument } from "@/types/knowledge";

function statusLabel(s: string) {
  if (s === "indexed") return { text: "就绪", className: "bg-green-500/10 text-green-500" };
  if (s === "indexing") return { text: "处理中", className: "bg-blue-500/10 text-blue-500" };
  if (s === "failed") return { text: "失败", className: "bg-red-500/10 text-red-500" };
  return { text: "待处理", className: "bg-muted text-muted-foreground" };
}

export default function KnowledgePage() {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showUpload, setShowUpload] = useState(false);

  useEffect(() => {
    knowledgeApi.list().then((res) => {
      setDocs(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filtered = docs.filter(
    (d) => !search || d.filename.toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = async (id: string) => {
    try {
      await knowledgeApi.delete(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch {}
  };

  return (
    <PageContainer>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">知识库</h1>
          <p className="mt-1 text-sm text-muted-foreground">管理和搜索文档知识</p>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {showUpload ? "收起" : "上传文档"}
        </button>
      </div>

      {showUpload && (
        <div className="mb-6">
          <FileUpload />
        </div>
      )}

      <div className="mb-4">
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索文档..."
            className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:border-primary/50"
          />
        </div>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
            <FileText className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-sm font-medium">暂无文档</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            {search ? "未找到匹配的文档" : "上传文档开始构建知识库"}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground text-xs">名称</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground text-xs hidden sm:table-cell">类型</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground text-xs hidden md:table-cell">大小</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground text-xs hidden md:table-cell">分片数</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground text-xs">状态</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground text-xs hidden lg:table-cell">日期</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground text-xs">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((doc) => {
                const st = statusLabel(doc.status);
                return (
                  <tr key={doc.id} className="hover:bg-muted/20">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                        <span className="truncate max-w-[200px]">{doc.filename}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell text-xs">
                      {doc.file_type || (doc.filename.split(".").pop() || "").toUpperCase()}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground hidden md:table-cell text-xs">
                      {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : "-"}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground hidden md:table-cell text-xs">
                      {doc.chunk_count ?? "-"}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${st.className}`}>
                        {st.text}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground hidden lg:table-cell text-xs">
                      {formatRelativeTime(doc.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="rounded p-1 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </PageContainer>
  );
}
