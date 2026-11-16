import { useEffect, useState } from "react";
import { api } from "../services/api";
import { ApiError } from "../services/apiClient";

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.details as { detail?: string | { message?: string } | { msg: string }[] } | undefined;
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return "Confira os campos obrigatórios e os participantes selecionados.";
    if (detail?.message) return detail.message;
    if (error.status === 401) return "Sua sessão expirou. Entre novamente para continuar.";
  }
  return "Não foi possível concluir a operação. Confira sua conexão e tente novamente.";
}

export function useResource<T>(path: string) {
  const [data, setData] = useState<T>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    api.request<T>(path, { signal: controller.signal }).then((value) => {
      if (!controller.signal.aborted) setData(value);
    }).catch((failure) => {
      if (!controller.signal.aborted) setError(errorMessage(failure));
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [path, version]);
  return { data, loading, error, reload: () => setVersion((v) => v + 1) };
}
