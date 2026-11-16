import { useState } from "react";
import type { FormEvent } from "react";
import { useApp } from "../state/AppContext";
import { api } from "../services/api";
import { errorMessage } from "../hooks/useResource";
import type { User } from "../types";
import { communityName } from "../types";
import ResourceState from "../components/ResourceState";
export default function ProfilePage() {
  const { user, authLoading, setUser, catalog } = useApp();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const data = new FormData(event.currentTarget);
    try {
      const profile = await api.request<User>("/auth/profile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: data.get("username"), community_id: Number(data.get("community")) }) });
      if (profile) { setUser(profile); catalog.reload(); window.location.hash = "/partidas/nova"; }
    } catch (failure) { setError(errorMessage(failure)); } finally { setBusy(false); }
  }
  if (authLoading) return <ResourceState loading/>;
  if (!user) return <div className="state-panel"><h1>Seu lugar à mesa.</h1><p>Entre ou crie sua conta antes de escolher sua identidade.</p><a href="#/entrar" className="button primary">Acessar minha conta</a></div>;
  if (!user.needs_profile) return <div className="state-panel"><h1>Você já faz parte da crônica.</h1><p>Seu perfil está pronto, {user.username}.</p><a href="#/partidas/nova" className="button primary">Registrar uma partida</a><details className="governance-heading"><summary>Identificação da minha conta</summary><p>Seu identificador pode ser usado por um administrador para localizar sua conta.</p><code className="account-id">{user.id}</code><p>Papel atual: {user.role || "USER"}</p></details></div>;
  return <div className="account-onboarding"><div className="eyebrow">PRIMEIRO, SUA IDENTIDADE</div><h1>Como a mesa<br/>vai lembrar de você?</h1><p>Escolha um nome público e sua comunidade principal. Você poderá jogar em outras comunidades também.</p><ResourceState loading={catalog.loading} error={catalog.error} retry={catalog.reload}><form className="form-card" onSubmit={(event) => { void submit(event); }}><label><span>Nome público</span><input name="username" required minLength={3} maxLength={40} autoComplete="nickname" placeholder="Seu nome ou apelido"/></label><label><span>Comunidade principal</span><select name="community" required defaultValue=""><option value="" disabled>Selecione uma comunidade</option>{catalog.data?.communities.map((community) => <option key={community.id} value={community.id}>{communityName(community)} · {community.city}/{community.state_code}</option>)}</select></label>{error && <div className="inline-error" role="alert">{error}</div>}<button className="button primary full" disabled={busy}>{busy ? "Guardando sua identidade…" : "Concluir perfil e continuar"}</button></form></ResourceState></div>;
}
