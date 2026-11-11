import { useApp } from "../state/AppContext";
import { useResource } from "../hooks/useResource";
import type { History } from "../types";
import { communityName } from "../types";
import ResourceState from "../components/ResourceState";
import MatchCard from "../components/MatchCard";
import { Crest } from "../components/BrandHeader";
export default function HomePage() {
  const { catalog, user } = useApp();
  const history = useResource<History>("/matches/?limit=3");
  const data = catalog.data;
  return <><div className="eyebrow">BEM-VINDO AO SEU PRÓXIMO CAPÍTULO</div><div className="page-heading"><div><h1>Todo encontro merece<br/>uma <em>boa história.</em></h1><p>Reúna sua comunidade. Registre a partida.<br className="desktop-break"/> Guarde o que aconteceu ao redor da mesa.</p></div><div className="hero-seal"><Crest/><span>JOGAR · REGISTRAR · PERTENCER</span></div></div>
    <div className="hero-actions"><a className="button primary" href="#/partidas/nova"><span aria-hidden="true">✦</span> Registrar uma partida</a><a className="text-link" href="#/comunidades">Explorar comunidades <span aria-hidden="true">✦</span></a></div>
    <ResourceState loading={catalog.loading} error={catalog.error} retry={catalog.reload}>{data && <><section className="stats-grid" aria-label="A comunidade em números"><div className="stat"><span>✦</span><div><strong>{data.communities.length}</strong><p>Comunidades</p></div></div><div className="stat"><span>✦</span><div><strong>{data.players.length}</strong><p>Identidades na mesa</p></div></div><div className="stat"><span>✦</span><div><strong>{data.verified_matches}</strong><p>Partidas verificadas</p></div></div></section>
    <div className="home-columns"><section><div className="section-heading"><div className="eyebrow">AS ÚLTIMAS CRÔNICAS</div><a href="#/historico" className="text-link">Ver histórico →</a></div><h2>Os encontros recentes</h2><ResourceState loading={history.loading} error={history.error} retry={history.reload} empty={history.data?.items.length === 0 ? "Registre a primeira partida e comece uma nova crônica." : undefined}>{history.data?.items.map((match) => <MatchCard key={match.id} match={match} communities={data.communities}/>)}</ResourceState></section>
    <aside className="community-feature"><div className="eyebrow">ENCONTRE SUA MESA</div><h2>Uma comunidade,<br/>muitas histórias.</h2><p>O jogo aproxima. A comunidade faz você voltar.</p>{data.communities.slice(0, 3).map((c) => <a className="community-mini" key={c.id} href={`#/historico?community=${c.id}`}><span className="community-monogram">{communityName(c).slice(0, 1)}</span><span><strong>{communityName(c)}</strong><small>{c.city} · {c.state_code}</small></span><b>✦</b></a>)}<a className="button secondary" href="#/comunidades">Conhecer as comunidades</a></aside></div></>}</ResourceState>
    <div className="oath"><span aria-hidden="true">✦</span><div><strong>Sua história continua sendo sua.</strong><p>Sem cotas de partidas. Resultados pendentes não contam nas estatísticas oficiais.</p></div><span className="oath-signature">{user ? `Boa jornada, ${user.username}.` : "A mesa está posta."}</span></div>
  </>;
}
