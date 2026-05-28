"use client";
export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h2 className="text-2xl font-bold">出错了</h2>
      <button onClick={reset} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90">重试</button>
    </div>
  );
}
