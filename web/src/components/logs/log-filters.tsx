"use client";

import { Search, X } from "lucide-react";
import type { LogLevel } from "@/types/log";

const levels: LogLevel[] = ["DEBUG", "INFO", "WARN", "ERROR"];

interface Props {
  selectedLevels: LogLevel[];
  onLevelsChange: (levels: LogLevel[]) => void;
  search: string;
  onSearchChange: (v: string) => void;
  source: string;
  onSourceChange: (v: string) => void;
  autoScroll: boolean;
  onAutoScrollChange: (v: boolean) => void;
}

export function LogFilters({
  selectedLevels,
  onLevelsChange,
  search,
  onSearchChange,
  source,
  onSourceChange,
  autoScroll,
  onAutoScrollChange,
}: Props) {
  const toggleLevel = (level: LogLevel) => {
    if (selectedLevels.includes(level)) {
      onLevelsChange(selectedLevels.filter((l) => l !== level));
    } else {
      onLevelsChange([...selectedLevels, level]);
    }
  };

  const hasActiveFilters = selectedLevels.length < 4 || search || source;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="搜索日志..."
            className="w-full rounded-lg border bg-background py-2 pl-10 pr-4 text-sm outline-none focus:border-primary/50"
          />
        </div>
        <input
          value={source}
          onChange={(e) => onSourceChange(e.target.value)}
          placeholder="来源过滤"
          className="w-32 rounded-lg border bg-background px-3 py-2 text-xs outline-none focus:border-primary/50"
        />
        <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => onAutoScrollChange(e.target.checked)}
            className="rounded border-border"
          />
          自动滚动
        </label>
        {hasActiveFilters && (
          <button
            onClick={() => {
              onLevelsChange(["DEBUG", "INFO", "WARN", "ERROR"]);
              onSearchChange("");
              onSourceChange("");
            }}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <X className="h-3 w-3" /> 清除
          </button>
        )}
      </div>
      <div className="flex gap-1">
        {levels.map((level) => {
          const active = selectedLevels.includes(level);
          const colorMap: Record<string, string> = {
            ERROR: "border-red-500/30 text-red-500 bg-red-500/10",
            WARN: "border-yellow-500/30 text-yellow-500 bg-yellow-500/10",
            INFO: "border-blue-500/30 text-blue-500 bg-blue-500/10",
            DEBUG: "border-muted text-muted-foreground bg-muted/30",
          };
          return (
            <button
              key={level}
              onClick={() => toggleLevel(level)}
              className={`rounded-md border px-2.5 py-1 text-[10px] font-medium transition-all ${
                active
                  ? colorMap[level]
                  : "border-transparent text-muted-foreground/40"
              }`}
            >
              {level}
            </button>
          );
        })}
      </div>
    </div>
  );
}
