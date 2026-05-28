"use client";

import { ArrowUp, ArrowDown } from "lucide-react";

interface Props {
  title: string;
  value: string;
  description?: string;
  trend?: { value: number; positive: boolean };
  icon?: React.ReactNode;
}

export function StatsCard({ title, value, description, trend, icon }: Props) {
  return (
    <div className="rounded-xl border bg-card p-4 text-card-foreground shadow-sm">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        {icon && (
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1 text-xs">
          {trend.positive ? (
            <ArrowUp className="h-3 w-3 text-green-500" />
          ) : (
            <ArrowDown className="h-3 w-3 text-red-500" />
          )}
          <span className={trend.positive ? "text-green-500" : "text-red-500"}>
            {trend.value}%
          </span>
          <span className="text-muted-foreground">较上月</span>
        </div>
      )}
    </div>
  );
}
