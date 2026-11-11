import { useState } from "react";
import type { FormEvent } from "react";
import { useApp } from "../state/AppContext";
import { useResource, errorMessage } from "../hooks/useResource";
import { api } from "../services/api";
import type { Page, Review } from "../types";
import { communityName } from "../types";
import MatchCard from "../components/MatchCard";
import ResourceState from "../components/ResourceState";

function ReviewPanel({ matchId }: { matchId: number }) {
  const { catalog } = useApp();
  const review = useResource<Review>(`/moderation/matches/${matchId}`);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  async function resolve(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const fields = new FormData(event.currentTarget);
    try {
      await api.request(`/moderation/matches/${matchId}/resolution`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision: fields.get("decision"), reason: fields.get("reason") }) });
      setNotice("Decisão registrada com justificativa e autoria na trilha de auditoria."); review.reload(); catalog.reload();
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <><a href="#/moderacao" className="text-link">← Voltar às disputas</a><ResourceState loading={review.loading} error={review.error} retry={review.reload}>{review.data && <>
    <h2 className="governance-heading">Análise da partida #{matchId}</h2><MatchCard match={review.data} communities={catalog.data?.communities || []}/>
    <div className="notice">{review.data.dispute_reason || "Este registro não contém o motivo original da contestação. Consulte os participantes antes de decidir."}</div>
    {notice && <div role="status" className="notice">{notice}</div>}
    {review.data.self_involved ? <div className="state-panel"><h2>Outra pessoa precisa analisar.</h2><p>Você publicou este registro ou participou da partida. Encaminhe a disputa a outro moderador autorizado ou administrador que não esteja envolvido.</p></div> : review.data.status === "DISPUTED" ? <form className="form-card resolution-form" onSubmit={(event) => { void resolve(event); }}>
      <h2>Registrar decisão</h2><p>A decisão preserva os participantes e o resultado informado. Validar torna a partida verificada; cancelar a exclui das estatísticas.</p>
      <label><span>Decisão</span><select name="decision" required defaultValue=""><option disabled value="">Selecione após analisar</option><option value="VERIFY">Validar o resultado registrado</option><option value="CANCEL">Cancelar a partida</option></select></label>
      <label><span>Justificativa da decisão</span><textarea name="reason" required minLength={10} maxLength={2000} rows={5} placeholder="Descreva os fatos e as informações que sustentam sua decisão."/></label>
      {error && <div className="inline-error" role="alert">{error}</div>}<button className="button primary" disabled={busy}>{busy ? "Registrando decisão…" : "Concluir análise e registrar decisão"}</button>
    </form> : <div className="notice">Esta partida não possui uma disputa aberta.</div>}
    <h2 className="governance-heading">Decisões registradas</h2>{review.data.resolution_history.length === 0 ? <p>Nenhuma decisão registrada para esta partida.</p> : review.data.resolution_history.map((event) => <article className="audit-card" key={event.id}><strong>{event.actor || "Conta indisponível"} · {new Date(event.occurred_at).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}</strong><p>{event.reason}</p><small>{String(event.previous.status)} → {String(event.next.status)}</small></article>)}
  </>}</ResourceState></>;
}

export default function ModerationPage() {
  const { user, catalog } = useApp();
  const [community, setCommunity] = useState("");
  const [offset, setOffset] = useState(0);
  const history = useResource<Page<Review>>(`/moderation/matches?limit=20&offset=${offset}${community ? `&community_id=${community}` : ""}`);
  const selected = new URLSearchParams(window.location.hash.split("?")[1]).get("match");
  const communities = catalog.data?.communities.filter((c) => user?.role === "ADMIN" || user?.moderated_community_ids?.includes(c.id)) || [];
  return <><div className="eyebrow">CUIDAR DA CONFIANÇA DA MESA</div><h1>Moderação</h1><p>{user?.role === "ADMIN" ? "Disputas de todas as comunidades." : "Disputas das comunidades sob sua moderação."}</p>
    {selected ? Number.isSafeInteger(Number(selected)) && Number(selected) > 0 ? <ReviewPanel matchId={Number(selected)}/> : <div role="alert">Identificador de partida inválido.</div> : <>
      <div className="filter-bar"><label><span>Comunidade</span><select value={community} onChange={(e) => { setCommunity(e.target.value); setOffset(0); }}><option value="">Todas as comunidades autorizadas</option>{communities.map((c) => <option key={c.id} value={c.id}>{communityName(c)}</option>)}</select></label><button className="button secondary" onClick={history.reload}>Atualizar disputas</button></div>
      <ResourceState loading={history.loading} error={history.error} retry={history.reload} empty={history.data?.items.length === 0 ? "Não há partidas contestadas nas comunidades selecionadas." : undefined}>{history.data?.items.map((match) => <section key={match.id} className="review-summary"><MatchCard match={match} communities={catalog.data?.communities || []}/><a href={`#/moderacao?match=${match.id}`} className="button secondary">Analisar partida #{match.id}{match.self_involved ? " · requer outro responsável" : ""}</a></section>)}</ResourceState>
      <div className="pagination"><button className="button secondary" disabled={offset === 0 || history.loading} onClick={() => setOffset((v) => Math.max(0, v - 20))}>Anteriores</button><span>Página {offset / 20 + 1}</span><button className="button secondary" disabled={history.loading || !history.data || offset + 20 >= history.data.total} onClick={() => setOffset((v) => v + 20)}>Próximas</button></div>
    </>}
  </>;
}
