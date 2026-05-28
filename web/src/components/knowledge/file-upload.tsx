"use client";

import { useState, useRef, type DragEvent } from "react";
import { Upload, File, X, FileText } from "lucide-react";

interface UploadFile {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: "uploading" | "done" | "error";
}

interface Props {
  onUpload?: (files: File[]) => Promise<void>;
}

export function FileUpload({ onUpload }: Props) {
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState<UploadFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = (fileList: FileList) => {
    const newFiles = Array.from(fileList).map((f) => ({
      id: crypto.randomUUID(),
      name: f.name,
      size: f.size,
      progress: 0,
      status: "uploading" as const,
    }));
    setFiles((prev) => [...prev, ...newFiles]);

    // Simulate upload progress
    newFiles.forEach((nf) => {
      let pct = 0;
      const interval = setInterval(() => {
        pct += Math.random() * 30;
        if (pct >= 100) {
          pct = 100;
          clearInterval(interval);
          setFiles((prev) =>
            prev.map((f) => f.id === nf.id ? { ...f, progress: 100, status: "done" as const } : f)
          );
        } else {
          setFiles((prev) =>
            prev.map((f) => f.id === nf.id ? { ...f, progress: Math.round(pct) } : f)
          );
        }
      }, 300);
    });
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed p-8 transition-colors ${
          dragging ? "border-primary bg-primary/5" : "border-muted-foreground/20 hover:border-muted-foreground/40"
        }`}
      >
        <Upload className="h-8 w-8 text-muted-foreground" />
        <div className="text-center">
          <p className="text-sm font-medium">
            {dragging ? "释放以上传" : "拖拽文件到此处，或点击上传"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            支持 PDF、Word、TXT、Markdown 等格式
          </p>
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.doc,.docx,.txt,.md,.csv"
        className="hidden"
        onChange={(e) => e.target.files && addFiles(e.target.files)}
      />

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((f) => (
            <div key={f.id} className="flex items-center gap-3 rounded-lg border bg-card p-3">
              <FileText className="h-8 w-8 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{f.name}</p>
                <p className="text-xs text-muted-foreground">{formatSize(f.size)}</p>
                {f.status === "uploading" && (
                  <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-300"
                      style={{ width: `${f.progress}%` }}
                    />
                  </div>
                )}
              </div>
              <div className="shrink-0">
                {f.status === "done" ? (
                  <span className="text-xs text-green-500">已完成</span>
                ) : f.status === "error" ? (
                  <span className="text-xs text-red-500">失败</span>
                ) : (
                  <span className="text-xs text-muted-foreground">{f.progress}%</span>
                )}
              </div>
              <button
                onClick={() => removeFile(f.id)}
                className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
