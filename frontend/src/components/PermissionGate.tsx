import type { ReactNode } from "react";
import type { Role } from "../types";
import { useApp } from "../state/AppContext";
import { hasRole } from "../services/permissions";
import ResourceState from "./ResourceState";

export default function PermissionGate({ allowed, children }: { allowed: readonly Role[]; children: ReactNode }) {
  const { user, authLoading, authError, refreshIdentity } = useApp();
  if (authLoading) return <ResourceState loading/>;
  if (authError) return <ResourceState error={authError} retry={() => { void refreshIdentity(); }}/>;
  if (!user) return <div className="state-panel"><h1>Entre na sua conta.</h1><p>Esta área exige autenticação e permissões específicas.</p><a className="button primary" href="#/entrar">Acessar minha conta</a></div>;
  if (!hasRole(user, allowed)) return <div className="state-panel" role="alert"><h1>Acesso restrito.</h1><p>Sua conta não possui permissão para esta área.</p><a href="#/" className="button secondary">Voltar ao início</a></div>;
  return children;
}
