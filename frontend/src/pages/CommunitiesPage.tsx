import { useApp } from "../state/AppContext";
import { communityName } from "../types";
import ResourceState from "../components/ResourceState";
export default function CommunitiesPage() {
  const { catalog } = useApp();
  return <><div className="eyebrow">LUGARES PARA PERTENCER</div><div className="section-title"><div><h1>Comunidades</h1><p>Encontre sua mesa e acompanhe as histórias de quem joga com você.</p></div><span className="page-symbol" aria-hidden="true">✦</span></div><ResourceState loading={catalog.loading} error={catalog.error} retry={catalog.reload} empty={catalog.data?.communities.length === 0 ? "Nenhuma comunidade foi cadastrada ainda." : undefined}><div className="cards-grid">{catalog.data?.communities.map((c) => <article className="community-card" key={c.id}><div className="community-banner"><span>{communityName(c).slice(0, 1)}</span><small>{c.state_code}</small></div><div className="community-card-body"><div className="eyebrow">{c.city} · {c.state_code}</div><h2>{communityName(c)}</h2><p>{c.description || "Um lugar para compartilhar encontros e construir histórias de jogo."}</p><div className="card-bottom"><span>✦ {catalog.data?.players.filter((p) => p.community_id === c.id).length} jogadores</span><a href={`#/historico?community=${c.id}`} className="text-link">Ver encontros →</a></div></div></article>)}</div></ResourceState></>;
}
