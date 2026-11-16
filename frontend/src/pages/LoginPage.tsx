import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import type { User } from "../types";
import { useApp } from "../state/AppContext";
import { errorMessage } from "../hooks/useResource";
import { Crest } from "../components/BrandHeader";
export default function LoginPage() {
  const { setUser, user } = useApp();
  const [mode, setMode] = useState<"login" | "signup" | "recover">("login");
  const [error, setError] = useState("");
  const parameters = new URLSearchParams(window.location.hash.split("?")[1]);
  const [notice, setNotice] = useState(parameters.has("confirmation") ? "Não foi possível confirmar esse link. Ele pode ter expirado. Entre na conta ou solicite a recuperação do acesso." : parameters.has("password") ? "Senha atualizada. Entre com sua nova senha." : "");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    const values = new FormData(event.currentTarget);
    const email = values.get("email");
    try {
      if (mode === "recover") {
        const result = await api.request<{ message: string }>("/auth/recover", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
        setNotice(result?.message || "Confira seu e-mail para continuar.");
      } else {
        const result = await api.request<User | { confirmation_required: boolean; user?: User }>(`/auth/${mode}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password: values.get("password") }) });
        if (result && "confirmation_required" in result) {
          if (result.confirmation_required) { setNotice("Conta solicitada. Abra o link de confirmação enviado ao seu e-mail para continuar. Se já tem uma conta e esqueceu a senha, use Recuperar acesso."); }
          else if (result.user) { setUser(result.user); window.location.hash = result.user.needs_profile ? "/perfil" : "/partidas/nova"; }
        } else if (result) { setUser(result); window.location.hash = result.needs_profile ? "/perfil" : "/partidas/nova"; }
      }
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }
  if (user) return <div className="state-panel"><h1>Boa jornada{user.username ? `, ${user.username}` : ""}.</h1><p>{user.needs_profile ? "Falta escolher seu nome público e comunidade." : "Sua conta já está conectada."}</p><a className="button primary" href={user.needs_profile ? "#/perfil" : "#/partidas/nova"}>{user.needs_profile ? "Completar meu perfil" : "Registrar uma partida"}</a></div>;
  return <div className="login-layout"><div className="login-story"><Crest/><div className="eyebrow">SEU LUGAR À MESA</div><h1>Entre para escrever<br/>o próximo capítulo.</h1><p>Uma conta, uma identidade.<br/>Encontros que continuam com você.</p><span className="ornament">✦ ───── ✦</span></div><form key={mode} className="form-card login-form" onSubmit={(event) => { void submit(event); }}><div className="account-tabs"><button type="button" className={mode === "login" ? "text-button selected" : "text-button"} onClick={() => { setMode("login"); setError(""); setNotice(""); }}>Entrar</button><button type="button" className={mode === "signup" ? "text-button selected" : "text-button"} onClick={() => { setMode("signup"); setError(""); setNotice(""); }}>Criar conta</button></div><div className="eyebrow">{mode === "signup" ? "SUA PRIMEIRA PÁGINA" : mode === "recover" ? "RECUPERAR ACESSO" : "BEM-VINDO DE VOLTA"}</div><h2>{mode === "signup" ? "Crie sua conta" : mode === "recover" ? "Volte para a mesa" : "Acessar sua conta"}</h2><p>{mode === "signup" ? "Você escolhe o e-mail e a senha. Depois, cria sua identidade na comunidade." : mode === "recover" ? "Enviaremos um link para você definir uma nova senha." : "Use sua conta do Scroll of Encounters."}</p><label><span>E-mail</span><input name="email" type="email" autoComplete="username" required placeholder="voce@exemplo.com"/></label>{mode !== "recover" && <label><span>Senha</span><input name="password" type="password" minLength={mode === "signup" ? 8 : undefined} autoComplete={mode === "signup" ? "new-password" : "current-password"} required/>{mode === "signup" && <small className="form-note">Use pelo menos oito caracteres.</small>}</label>}{notice && <div role="status" className="notice">{notice}</div>}{error && <div role="alert" className="inline-error">{error}</div>}<button className="button primary full" disabled={busy}>{busy ? "Um instante…" : mode === "signup" ? "Criar minha conta" : mode === "recover" ? "Enviar link de recuperação" : "Entrar"}<span aria-hidden="true">✦</span></button>{mode === "login" && <button type="button" className="text-button recover-link" onClick={() => { setMode("recover"); setError(""); setNotice(""); }}>Esqueci minha senha</button>}<small className="form-note">Sua autoria é validada pela conta autenticada. Não compartilhe sua senha ou links de acesso.</small></form></div>;
}
