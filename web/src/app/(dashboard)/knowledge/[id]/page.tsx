"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileText, Search, Trash2 } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { knowledgeApi } from "@/api/knowledge";
import { formatRelativeTime } from "@/lib/utils";
import type { KnowledgeDocument, SearchResult } from "@/types/knowledge";

export default function KnowledgeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [doc, setDoc] = useState<KnowledgeDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    // Get from list since there's no single doc endpoint
    knowledgeApi.list().then((res) => {
      const found = res.data.find((d) => d.id === id);
      setDoc(found || null);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [id]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await knowledgeApi.search(searchQuery);
      setResults(res.data);
    } catch {} finally {
      setSearching(false);
    }
  };

  const handleDelete = async () => {
    try {
      await knowledgeApi.delete(id);
      router.push("/knowledge");
    } catch {}
  };

  if (loading) {
    return (
      <PageContainer>
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
      </PageContainer>
    );
  }

  if (!doc) {
    return (
      <PageContainer>
        <div className="flex flex-col items-center justify-center py-20">
          <FileText className="h-12 w-12 text-muted-foreground" />
          <h2 className="mt-4 text-lg font-semibold">文档不存在</h2>
          <button onClick={() => router.push("/knowledge")} className="mt-2 text-sm text-primary hover:underline">
            返回知识库
          </button>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer className="max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/knowledge")}
            className="rounded-md p-1 text-muted-foreground hover:bg-accent"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-lg font-bold">{doc.filename}</h1>
            <p className="text-xs text-muted-foreground">
              {(doc.file_size / 1024).toFixed(1)} KB · {doc.chunk_count} 个分片 · 上传于 {formatRelativeTime(doc.created_at)}
            </p>
          </div>
        </div>
        <button
          onClick={handleDelete}
          className="flex items-center gap-1 rounded-lg border border-destructive/20 px-3 py-2 text-xs text-destructive hover:bg-destructive/10"
        >
          <Trash2 className="h-3.5 w-3.5" /> 删除
        </button>
      </div>

      <div className="mb-6">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="在文档中搜索..."
              className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:border-primary/50"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={searching}
            className="rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            搜索
          </button>
        </div>
      </div>

      {searching ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : results.length > 0 ? (
        <div className="space-y-3">
          {results.map((r) => (
            <div key={r.id} className="rounded-lg border bg-card p-4">
              <div className="mb-2 flex items-center gap-2">
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                  相似度: {(r.score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-sm leading-relaxed text-muted-foreground">{r.content}</p>
            </div>
          ))}
        </div>
      ) : searchQuery ? (
        <p className="text-center text-sm text-muted-foreground py-10">无搜索结果</p>
      ) : null}
    </PageContainer>
  );
}
