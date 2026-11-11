import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { Catalog, User } from "../types";
import { useResource } from "../hooks/useResource";
import { api } from "../services/api";
import { ApiError } from "../services/apiClient";

type State = { catalog: ReturnType<typeof useResource<Catalog>>; user: User | null; authLoading: boolean; setUser: (user: User | null) => void; logout: () => Promise<void> };
const AppContext = createContext<State | null>(null);
export function AppProvider({ children }: { children: ReactNode }) {
  const catalog = useResource<Catalog>("/catalog");
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  useEffect(() => {
    let active = true;
    async function restore() {
      try {
        let identity: User | undefined;
        try { identity = await api.request<User>("/auth/me"); }
        catch (error) {
          if (!(error instanceof ApiError) || error.status !== 401) throw error;
          identity = await api.request<User>("/auth/refresh", { method: "POST" });
        }
        if (active && identity) setUser(identity);
      } catch { if (active) setUser(null); }
      finally { if (active) setAuthLoading(false); }
    }
    void restore();
    return () => { active = false; };
  }, []);
  async function logout() { await api.request("/auth/logout", { method: "POST" }); setUser(null); }
  return <AppContext.Provider value={{ catalog, user, authLoading, setUser, logout }}>{children}</AppContext.Provider>;
}
export function useApp() { const state = useContext(AppContext); if (!state) throw new Error("AppProvider ausente"); return state; }
