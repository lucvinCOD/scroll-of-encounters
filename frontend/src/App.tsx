import { useEffect, useState } from "react";
import { AppProvider } from "./state/AppContext";
import AppShell from "./components/layout/AppShell";
import HomePage from "./pages/HomePage";
import CommunitiesPage from "./pages/CommunitiesPage";
import PlayersPage from "./pages/PlayersPage";
import HistoryPage from "./pages/HistoryPage";
import LoginPage from "./pages/LoginPage";
import ProfilePage from "./pages/ProfilePage";
import PasswordPage from "./pages/PasswordPage";
import RegisterMatchPage from "./pages/RegisterMatchPage";
import PermissionGate from "./components/PermissionGate";
import AdminPage from "./pages/AdminPage";
import ModerationPage from "./pages/ModerationPage";
function Navigation() {
  const [route, setRoute] = useState(window.location.hash.slice(1) || "/");
  useEffect(() => { const navigate = () => { setRoute(window.location.hash.slice(1) || "/"); window.scrollTo(0, 0); }; window.addEventListener("hashchange", navigate); return () => window.removeEventListener("hashchange", navigate); }, []);
  const path = route.split("?")[0];
  const pages = { "/": <HomePage/>, "/comunidades": <CommunitiesPage/>, "/jogadores": <PlayersPage/>, "/historico": <HistoryPage/>, "/perfil": <ProfilePage/>, "/nova-senha": <PasswordPage/>, "/entrar": <LoginPage/>, "/partidas/nova": <RegisterMatchPage/>, "/moderacao": <PermissionGate allowed={["MODERATOR", "ADMIN"]}><ModerationPage/></PermissionGate>, "/administracao": <PermissionGate allowed={["ADMIN"]}><AdminPage/></PermissionGate> };
  return <AppShell route={route}>{pages[path as keyof typeof pages] || <div className="state-panel"><h1>Esta página não está no mapa.</h1><a href="#/" className="button primary">Voltar ao início</a></div>}</AppShell>;
}
export default function App() { return <AppProvider><a className="skip-link" href="#main-content" onClick={(event) => { event.preventDefault(); document.getElementById("main-content")?.focus(); }}>Pular para o conteúdo</a><Navigation/></AppProvider>; }
