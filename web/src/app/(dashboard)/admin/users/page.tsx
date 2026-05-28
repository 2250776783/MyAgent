"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Users } from "lucide-react";
import { PageContainer } from "@/components/shared/page-container";
import { UserTable } from "@/components/admin/user-table";
import { adminApi } from "@/api/admin";

interface AdminUser {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

const mockUsers: AdminUser[] = [
  { id: "1", username: "admin", email: "admin@example.com", role: "ADMIN", is_active: true, created_at: "2025-01-01T00:00:00Z", last_login: "2025-05-28T00:00:00Z" },
  { id: "2", username: "alice", email: "alice@example.com", role: "USER", is_active: true, created_at: "2025-02-15T00:00:00Z", last_login: "2025-05-27T00:00:00Z" },
  { id: "3", username: "bob", email: "bob@example.com", role: "USER", is_active: false, created_at: "2025-03-10T00:00:00Z", last_login: "2025-04-01T00:00:00Z" },
];

export default function AdminUsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<AdminUser[]>(mockUsers);

  const handleRoleChange = (id: string, role: string) => {
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, role } : u)));
  };

  const handleToggleActive = (id: string, is_active: boolean) => {
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, is_active } : u)));
  };

  const handleDelete = (id: string) => {
    setUsers((prev) => prev.filter((u) => u.id !== id));
  };

  return (
    <PageContainer>
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => router.push("/admin")} className="rounded-md p-1 text-muted-foreground hover:bg-accent">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">用户管理</h1>
          <p className="mt-1 text-sm text-muted-foreground">查看和管理所有用户</p>
        </div>
      </div>
      <UserTable users={users} onRoleChange={handleRoleChange} onToggleActive={handleToggleActive} onDelete={handleDelete} />
    </PageContainer>
  );
}
