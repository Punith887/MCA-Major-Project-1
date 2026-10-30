import axios from "axios";

export const TOKEN_STORAGE_KEY = "aiops_access_token";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (
      axios.isAxiosError(error) &&
      error.response?.status === 401 &&
      !window.location.pathname.startsWith("/login")
    ) {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      window.dispatchEvent(new Event("aiops:session-expired"));
    }
    return Promise.reject(error);
  },
);

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError<{ detail?: string }>(error)) {
    return error.response?.data?.detail ?? fallback;
  }
  return fallback;
}
