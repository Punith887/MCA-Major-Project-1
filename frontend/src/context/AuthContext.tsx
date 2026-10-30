import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import { getCurrentUser, login as loginRequest } from "../services/auth";
import { TOKEN_STORAGE_KEY } from "../services/api";
import type { User } from "../types/api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!token) {
      setIsLoading(false);
      return;
    }

    getCurrentUser()
      .then(setUser)
      .catch(clearSession)
      .finally(() => setIsLoading(false));
  }, [clearSession]);

  useEffect(() => {
    window.addEventListener("aiops:session-expired", clearSession);
    return () => window.removeEventListener("aiops:session-expired", clearSession);
  }, [clearSession]);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await loginRequest(email, password);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, result.access_token);
    setUser(result.user);
  }, []);

  const signOut = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const value = useMemo(
    () => ({ user, isLoading, signIn, signOut }),
    [user, isLoading, signIn, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }
  return context;
}

export function useSignOutAndNavigate() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  return () => {
    signOut();
    navigate("/login", { replace: true });
  };
}
