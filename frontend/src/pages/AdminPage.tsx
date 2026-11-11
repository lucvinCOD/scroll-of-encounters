import { useState } from "react";
import type { FormEvent } from "react";
import { useApp } from "../state/AppContext";
import { useResource, errorMessage } from "../hooks/useResource";
import { api } from "../services/api";
import type { AdminAccount, AuditEvent, Page } from "../types";
import { communityName } from "../types";
import ResourceState from "../components/ResourceState";

const actions: Record<string, string> = { BOOTSTRAP_ADMIN: "Primeiro administrador", ADMIN_GRANTED: "Administrador designado", ADMIN_REVOKED: "Acesso administrativo removido", MODERATOR_GRANTED: "Moderador designado", MODERATOR_REVOKED: "Moderação removida", DISPUTE_RESOLVED: "Disputa resolvida" };

export default function AdminPage() {
  const { catalog, refreshIdentity } = useApp();
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [auditOffset, setAuditOffset] = useState(0);
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const users = useResource<Page<AdminAccount>>(`/admin/users?limit=20&offset=${offset}&q=${encodeURIComponent(query)}`);
  const audit = useResource<Page<AuditEvent>>(`/admin/audit?limit=20&offset=${auditOffset}`);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    const fields = new FormData(event.currentTarget);
    try {
      const result = await api.request<{ changed: boolean }>("/admin/moderators", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ profile_id: target, community_id: Number(fields.get("community")), enabled: fields.get("operation") === "grant", reason: fields.get("reason") }) });
      setNotice(result?.changed ? "Permissão atualizada e registrada na auditoria." : "Esse vínculo já estava no estado solicitado."); users.reload(); audit.reload(); await refreshIdentity();
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <><div className="eyebrow">GUARDIÕES DO SCROLL</div><div className="section-title"><div><h1>Administração</h1><p>Contas, vínculos de moderação e ações que preservam a confiança.</p></div><a href="#/moderacao" className="button secondary">Disputas de todas as comunidades</a></div>
    <h2>Contas e permissões</h2><div className="filter-bar"><label><span>Buscar nome público</span><input value={query} onChange={(e) => { setQuery(e.target.value); setOffset(0); setTarget(""); }} maxLength={80} type="search" placeholder="Nome ou apelido"/></label></div>
    <ResourceState loading={users.loading} error={users.error} retry={users.reload} empty={users.data?.items.length === 0 ? "Nenhuma conta encontrada." : undefined}><div className="account-list">{users.data?.items.map((account) => <article key={account.id} className={target === account.id ? "account-card selected" : "account-card"}><div><h3>{account.username}</h3><span className="badge guest">{account.role} · {account.status}</span><p>Comunidades moderadas: {account.moderated_community_ids.map((id) => { const c = catalog.data?.communities.find((item) => item.id === id); return c ? communityName(c) : `#${id}`; }).join(", ") || "nenhuma"}</p><small className="account-id">ID: {account.id}</small></div><button className="button secondary" type="button" onClick={() => { setTarget(account.id); setNotice(""); }}>Selecionar conta</button></article>)}</div></ResourceState>
    <div className="pagination"><button className="button secondary" disabled={offset === 0 || users.loading} onClick={() => { setOffset((v) => Math.max(0, v - 20)); setTarget(""); }}>Anteriores</button><span>Página {offset / 20 + 1}</span><button className="button secondary" disabled={users.loading || !users.data || offset + 20 >= users.data.total} onClick={() => { setOffset((v) => v + 20); setTarget(""); }}>Próximas</button></div>
    <form className="form-card assignment-form" onSubmit={(event) => { void submit(event); }}><h2>Designar ou remover moderador</h2><p>{target ? `Conta selecionada: ${users.data?.items.find((a) => a.id === target)?.username || target}` : "Selecione uma conta na lista acima."}</p><div className="field-grid"><label><span>Comunidade</span><select name="community" required defaultValue=""><option value="" disabled>Selecione uma comunidade</option>{catalog.data?.communities.map((c) => <option key={c.id} value={c.id}>{communityName(c)}</option>)}</select></label><label><span>Operação</span><select name="operation" required defaultValue="grant"><option value="grant">Designar moderador</option><option value="revoke">Remover vínculo de moderação</option></select></label></div><label><span>Justificativa</span><textarea name="reason" minLength={10} maxLength={2000} rows={3} required/></label>{error && <div role="alert" className="inline-error">{error}</div>}{notice && <div role="status" className="notice">{notice}</div>}<button className="button primary" disabled={busy || !target || !catalog.data}>{busy ? "Atualizando permissão…" : "Aplicar vínculo de moderação"}</button><p className="form-note">Acesso ADMIN exige um procedimento separado de operador autorizado. Este formulário concede apenas moderação na comunidade selecionada.</p></form>
    <h2 className="governance-heading">Trilha de auditoria</h2><ResourceState loading={audit.loading} error={audit.error} retry={audit.reload} empty={audit.data?.items.length === 0 ? "Nenhuma ação sensível registrada." : undefined}>{audit.data?.items.map((event) => <article className="audit-card" key={event.id}><strong>{actions[event.action || ""] || event.action} · #{event.id}</strong><p>{event.reason}</p><small>Por {event.actor || `Operador do banco (${event.database_actor || "identificado no registro"})`} · {new Date(event.occurred_at).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}</small><p className="form-note">{event.community_id && `Comunidade #${event.community_id} · `}{event.match_id && `Partida #${event.match_id} · `}{event.target_profile_id && `Conta ${event.target_profile_id}`}</p><details><summary>Ver alteração registrada</summary><pre className="audit-values">{JSON.stringify({ anterior: event.previous, atual: event.next }, null, 2)}</pre></details></article>)}</ResourceState>
    <div className="pagination"><button className="button secondary" disabled={auditOffset === 0 || audit.loading} onClick={() => setAuditOffset((v) => Math.max(0, v - 20))}>Anteriores</button><span>Página {auditOffset / 20 + 1}</span><button className="button secondary" disabled={audit.loading || !audit.data || auditOffset + 20 >= audit.data.total} onClick={() => setAuditOffset((v) => v + 20)}>Próximas</button></div>
  </>;
}
