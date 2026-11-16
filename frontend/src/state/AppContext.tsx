import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import type { Catalog, User } from "../types";
import { useResource } from "../hooks/useResource";
import { api } from "../services/api";
import { ApiError } from "../services/apiClient";
import { errorMessage } from "../hooks/useResource";

type State = { catalog: ReturnType<typeof useResource<Catalog>>; user: User | null; authLoading: boolean; authError: string; refreshIdentity: () => Promise<void>; setUser: (user: User | null) => void; logout: () => Promise<void> };
const AppContext = createContext<State | null>(null);
export function AppProvider({ children }: { children: ReactNode }) {
  const catalog = useResource<Catalog>("/catalog");
  const [user, setUserState] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const sessionRevision = useRef(0);
  const inFlight = useRef<Promise<void> | null>(null);
  const setUser = useCallback((identity: User | null) => {
    sessionRevision.current += 1;
    setUserState(identity); setAuthError(""); setAuthLoading(false);
  }, []);
  const refreshIdentity = useCallback(() => {
    if (inFlight.current) return inFlight.current;
    const revision = sessionRevision.current;
    const restore = async () => {
      try {
        let identity: User | undefined;
        try { identity = await api.request<User>("/auth/me"); }
        catch (error) {
          if (!(error instanceof ApiError) || error.status !== 401) throw error;
          identity = await api.request<User>("/auth/refresh", { method: "POST" });
        }
        if (revision === sessionRevision.current) { setUserState(identity || null); setAuthError(""); }
      } catch (error) {
        if (revision === sessionRevision.current) {
          setUserState(null);
          setAuthError(error instanceof ApiError && [401, 403].includes(error.status) ? "" : errorMessage(error));
        }
      } finally { if (revision === sessionRevision.current) setAuthLoading(false); }
    };
    // Eventos de foco/navegação compartilham uma verificação, sem refreshes paralelos.
    const pending: Promise<void> = restore().finally(() => {
      if (inFlight.current === pending) inFlight.current = null;
    });
    inFlight.current = pending;
    return pending;
  }, []);
  useEffect(() => {
    const check = () => { if (document.visibilityState !== "hidden") void refreshIdentity(); };
    check();
    window.addEventListener("focus", check);
    window.addEventListener("hashchange", check);
    document.addEventListener("visibilitychange", check);
    return () => {
      window.removeEventListener("focus", check);
      window.removeEventListener("hashchange", check);
      document.removeEventListener("visibilitychange", check);
    };
  }, [refreshIdentity]);
  async function logout() { await api.request("/auth/logout", { method: "POST" }); setUser(null); }
  return <AppContext.Provider value={{ catalog, user, authLoading, authError, refreshIdentity, setUser, logout }}>{children}</AppContext.Provider>;
}
export function useApp() { const state = useContext(AppContext); if (!state) throw new Error("AppProvider ausente"); return state; }
