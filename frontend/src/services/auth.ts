import type { TokenResponse, User } from "../types/api";
import { api } from "./api";

export interface RegisterPayload {
  full_name: string;
  email: string;
  password: string;
}

export async function register(payload: RegisterPayload): Promise<User> {
  const response = await api.post<User>("/auth/register", payload);
  return response.data;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const form = new URLSearchParams({ username: email, password });
  const response = await api.post<TokenResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
}
