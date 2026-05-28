import apiClient from "./client";
import type { AuthResponse, User } from "@/types/auth";

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<AuthResponse>("/auth/login", { email, password }).then((r) => r.data),
  register: (username: string, email: string, password: string) =>
    apiClient.post<AuthResponse>("/auth/register", { username, email, password }).then((r) => r.data),
  logout: () => apiClient.post("/auth/logout"),
  refresh: (refreshToken: string) =>
    apiClient.post<{ access_token: string; refresh_token: string }>("/auth/refresh", { refresh_token: refreshToken }).then((r) => r.data),
  getProfile: () => apiClient.get<User>("/auth/profile").then((r) => r.data),
  updatePassword: (oldPassword: string, newPassword: string) =>
    apiClient.put("/auth/password", { old_password: oldPassword, new_password: newPassword }),
};

