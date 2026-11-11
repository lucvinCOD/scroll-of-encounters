import { useState } from "react";
import type { ReactNode } from "react";
import BrandHeader from "../BrandHeader";
import { useApp } from "../../state/AppContext";
import { errorMessage } from "../../hooks/useResource";

const links = [["/", "⌂", "Início"], ["/comunidades", "⚑", "Comunidades"], ["/jogadores", "✦", "Jogadores"], ["/historico", "☷", "Histórico"], ["/partidas/nova", "+", "Registrar partida"]];
export default function AppShell({ children, route }: { children: ReactNode; route: string }) {
  const { user, logout } = useApp();
  const [error, setError] = useState("");
  const path = route.split("?")[0];
  return <div className="app-shell min-h-screen">
    <aside className="sidebar"><BrandHeader/><div className="nav-caption">SEU LIVRO DE ENCONTROS</div>
      <nav aria-label="Navegação principal">{links.map(([url, icon, title]) => <a key={url} href={`#${url}`} aria-current={path === url ? "page" : undefined} className={path === url ? "nav-link active" : "nav-link"}><span aria-hidden="true">{icon}</span>{title}{path === url && <b aria-hidden="true">✦</b>}</a>)}</nav>
      <div className="sidebar-footer"><span className="ornament">✦ ─── ✦</span><p>Grandes histórias começam<br/>ao redor de uma mesa.</p><small>COMUNIDADE PRIMEIRO</small></div>
    </aside>
    <div className="workspace"><header className="topbar"><span className="topbar-label">O LIVRO ESTÁ ABERTO <span aria-hidden="true">✦</span></span><div className="account">{user ? <><span className="avatar">{user.username.slice(0, 1).toUpperCase() || "?"}</span><a href="#/perfil">{user.username || "Completar perfil"}</a><button className="text-button" onClick={() => { void logout().catch((failure) => setError(errorMessage(failure))); }}>Sair</button></> : <a href="#/entrar" className="button small secondary">Entrar na guilda <span aria-hidden="true">✦</span></a>}</div></header>
    {error && <div role="alert" className="inline-error">{error}</div>}
    <main id="main-content" tabIndex={-1} className="main-content" key={route}>{children}<footer className="page-footer"><span>Scroll of Encounters</span><span>Feito para jogar. Construído para lembrar.</span><span aria-hidden="true">✦</span></footer></main></div>
  </div>;
}
