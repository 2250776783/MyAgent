"use client";

import { useState } from "react";
import { User, Camera } from "lucide-react";

interface Props {
  initialData: { username: string; email: string; avatar?: string };
  onSave: (data: { username: string; email: string }) => void;
}

export function ProfileForm({ initialData, onSave }: Props) {
  const [username, setUsername] = useState(initialData.username);
  const [email, setEmail] = useState(initialData.email);
  const [hasChanges, setHasChanges] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ username, email });
    setHasChanges(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-6 flex items-center gap-4">
        <div className="relative">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <User className="h-6 w-6 text-primary" />
          </div>
          <button className="absolute bottom-0 right-0 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <Camera className="h-3 w-3" />
          </button>
        </div>
        <div>
          <p className="text-sm font-medium">{username}</p>
          <p className="text-xs text-muted-foreground">{email}</p>
        </div>
      </div>
      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">用户名</label>
          <input
            value={username}
            onChange={(e) => { setUsername(e.target.value); setHasChanges(true); }}
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:border-primary/50"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">邮箱</label>
          <input
            value={email}
            onChange={(e) => { setEmail(e.target.value); setHasChanges(true); }}
            type="email"
            className="w-full rounded-lg border bg-background px-3 py-2 text-sm outline-none focus:border-primary/50"
          />
        </div>
        {hasChanges && (
          <button
            type="submit"
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            保存
          </button>
        )}
      </div>
    </form>
  );
}
