import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  clearToken,
  getMe,
  getToken,
  login as apiLogin,
  setToken,
  signup as apiSignup,
  type MeResponse,
} from "../services/api";


// ─── Types ───────────────────────────────────────────────────────────────────

type AuthUser = MeResponse;

type AuthContextValue = {
  user: AuthUser | null;
  learnerId: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, username: string, password: string, displayName?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ─── Provider ────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      clearToken();
      setUser(null);
    }
  }, []);

  // On mount: try to restore session from stored token
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
        return;
    }
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiLogin(email, password);
    setToken(res.access_token);
    await refreshUser();
  }, [refreshUser]);

  const signup = useCallback(async (
    email: string,
    username: string,
    password: string,
    displayName?: string,
  ) => {
    const res = await apiSignup(email, username, password, displayName);
    setToken(res.access_token);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        learnerId: user?.learner_id ?? null,
        loading,
        login,
        signup,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
