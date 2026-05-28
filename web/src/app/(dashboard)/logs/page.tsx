"use client";

import { useState, useEffect, useCallback } from "react";
import { ScrollText } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { LogFilters } from "@/components/logs/log-filters";
import { LogViewer } from "@/components/logs/log-viewer";
import { logsApi } from "@/api/logs";
import type { LogEntry as LogEntryType, LogLevel } from "@/types/log";

export default function LogsPage() {
  const [entries, setEntries] = useState<LogEntryType[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [selectedLevels, setSelectedLevels] = useState<LogLevel[]>(["ERROR", "WARN", "INFO", "DEBUG"]);
  const [autoScroll, setAutoScroll] = useState(true);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await logsApi.list({
        level: selectedLevels.length < 4 ? selectedLevels : undefined,
        search: search || undefined,
        source: source || undefined,
      });
      setEntries(res.data);
    } catch {} finally {
      setLoading(false);
    }
  }, [selectedLevels, search, source]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <PageContainer className="max-w-6xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">日志</h1>
        <p className="mt-1 text-sm text-muted-foreground">查看系统运行日志和调试信息</p>
      </div>

      <div className="mb-4">
        <LogFilters
          selectedLevels={selectedLevels}
          onLevelsChange={setSelectedLevels}
          search={search}
          onSearchChange={setSearch}
          source={source}
          onSourceChange={setSource}
          autoScroll={autoScroll}
          onAutoScrollChange={setAutoScroll}
        />
      </div>

      <LogViewer entries={entries} loading={loading} autoScroll={autoScroll} />
    </PageContainer>
  );
}
