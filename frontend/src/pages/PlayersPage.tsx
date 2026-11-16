import { useState } from "react";
import { useApp } from "../state/AppContext";
import { communityName } from "../types";
import ResourceState from "../components/ResourceState";
export default function PlayersPage() {
  const { catalog } = useApp();
  const [search, setSearch] = useState("");
  const [community, setCommunity] = useState("");
  const players = catalog.data?.players.filter((p) => p.display_name.toLocaleLowerCase().includes(search.toLocaleLowerCase()) && (!community || String(p.community_id) === community));
  return <><div className="eyebrow">QUEM DÁ VIDA À MESA</div><div className="section-title"><div><h1>Jogadores</h1><p>Identidades que permanecem. Histórias que se encontram.</p></div><span className="page-symbol" aria-hidden="true">✦</span></div><div className="filter-bar"><label className="search-label"><span>Buscar jogador</span><input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Nome ou apelido"/></label><label><span>Comunidade principal</span><select value={community} onChange={(e) => setCommunity(e.target.value)}><option value="">Todas as comunidades</option>{catalog.data?.communities.map((c) => <option key={c.id} value={c.id}>{communityName(c)}</option>)}</select></label></div><ResourceState loading={catalog.loading} error={catalog.error} retry={catalog.reload} empty={players?.length === 0 ? "Nenhum jogador encontrado com esses filtros." : undefined}><div className="players-grid">{players?.map((p) => { const c = catalog.data?.communities.find((item) => item.id === p.community_id); return <article className="player-card" key={p.id}><div className="player-avatar">{p.display_name.slice(0, 2).toUpperCase()}</div><div><h2>{p.display_name}</h2><p>{c ? communityName(c) : "Comunidade"}</p><span className={p.is_guest ? "badge guest" : "badge verified"}>{p.is_guest ? "Convidado persistente" : "Jogador registrado"}</span></div></article>; })}</div></ResourceState></>;
}
