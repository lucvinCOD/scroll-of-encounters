import { useState } from "react";
import type { FormEvent } from "react";
import { useApp } from "../state/AppContext";
import { api } from "../services/api";
import { errorMessage } from "../hooks/useResource";
import ResourceState from "../components/ResourceState";
export default function PasswordPage() {
  const { user, authLoading, setUser } = useApp();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const fields = new FormData(event.currentTarget); setError("");
    if (fields.get("password") !== fields.get("confirmation")) { setError("As senhas precisam ser iguais."); return; }
    setBusy(true);
    try { await api.request("/auth/password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: fields.get("password") }) }); setUser(null); window.location.hash = "/entrar?password=changed"; }
    catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  }
  if (authLoading) return <ResourceState loading/>;
  if (!user) return <div className="state-panel"><h1>Recupere seu acesso.</h1><p>Abra o link recebido por e-mail para definir uma nova senha.</p><a className="button primary" href="#/entrar">Voltar ao acesso</a></div>;
  return <div className="account-onboarding"><div className="eyebrow">UM NOVO COMEÇO</div><h1>Defina sua nova senha.</h1><form className="form-card" onSubmit={(event) => { void submit(event); }}><label><span>Nova senha</span><input name="password" type="password" minLength={8} required autoComplete="new-password"/></label><label><span>Repita a nova senha</span><input name="confirmation" type="password" minLength={8} required autoComplete="new-password"/></label>{error && <div className="inline-error" role="alert">{error}</div>}<button className="button primary full" disabled={busy}>{busy ? "Atualizando…" : "Salvar nova senha"}</button></form></div>;
}
