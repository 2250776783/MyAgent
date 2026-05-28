export type UserRole = "USER" | "ADMIN";
export interface User { id: string; username: string; email: string; avatar?: string; role: UserRole; created_at: string; is_active?: boolean; }
export interface LoginRequest { email: string; password: string; }
export interface RegisterRequest { username: string; email: string; password: string; }
export interface AuthResponse { access_token: string; refresh_token: string; user: User; }
export interface LoginFormValues { email: string; password: string; remember?: boolean; }
export interface RegisterFormValues { username: string; email: string; password: string; confirm_password: string; }

