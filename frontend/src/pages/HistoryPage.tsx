import { useState } from "react";
import { useApp } from "../state/AppContext";
import { useResource } from "../hooks/useResource";
import type { History } from "../types";
import { communityName } from "../types";
import ResourceState from "../components/ResourceState";
import MatchCard from "../components/MatchCard";
export default function HistoryPage() {
  const { catalog } = useApp();
  const initial = new URLSearchParams(window.location.hash.split("?")[1]).get("community") || "";
  const [community, setCommunity] = useState(initial);
  const [offset, setOffset] = useState(0);
  const history = useResource<History>(`/matches/?limit=20&offset=${offset}${community ? `&community_id=${encodeURIComponent(community)}` : ""}`);
  return <><div className="eyebrow">CADA PARTIDA, UM CAPÍTULO</div><div className="section-title"><div><h1>Histórico de encontros</h1><p>Resultados relatados pela comunidade. Só partidas verificadas contam nas estatísticas.</p></div><a className="button primary" href="#/partidas/nova">+ Registrar partida</a></div><div className="filter-bar"><label><span>Comunidade anfitriã</span><select value={community} onChange={(e) => { setCommunity(e.target.value); setOffset(0); }}><option value="">Todas as comunidades</option>{catalog.data?.communities.map((c) => <option key={c.id} value={c.id}>{communityName(c)}</option>)}</select></label><span className="filter-count">{history.data ? `${history.data.total} encontros registrados` : ""}</span></div><ResourceState loading={history.loading} error={history.error} retry={history.reload} empty={history.data?.items.length === 0 ? "Ainda não há partidas nesta seleção. Que tal começar uma história…" : undefined}>{history.data?.items.map((match) => <MatchCard key={match.id} match={match} communities={catalog.data?.communities || []}/>)}</ResourceState>{history.data && history.data.total > 20 && <div className="pagination"><button className="button secondary" disabled={offset === 0 || history.loading} onClick={() => setOffset((v) => Math.max(0, v - 20))}>← Anteriores</button><span>Página {offset / 20 + 1}</span><button className="button secondary" disabled={offset + 20 >= history.data.total || history.loading} onClick={() => setOffset((v) => v + 20)}>Próximos →</button></div>}</>;
}
