import type { Match, Community } from "../types";
import { communityName } from "../types";
const labels = { PENDING: "Aguardando validação", VERIFIED: "Verificada", DISPUTED: "Em disputa", CANCELLED: "Cancelada" };
export default function MatchCard({ match, communities }: { match: Match; communities: Community[] }) {
  const community = communities.find((c) => c.id === match.community_id);
  const winner = match.participants.find((p) => p.result === "WIN");
  const draw = match.participants.length > 0 && match.participants.every((p) => p.result === "DRAW");
  return <article className="match-card"><div className="match-date"><strong>{match.match_date.split("-")[2]}</strong><span>{match.match_date.split("-").slice(0, 2).reverse().join("/")}</span></div><div className="match-body"><div className="card-eyebrow">{match.format_name} <span>· ENCONTRO #{match.id}</span></div><h3>{community ? communityName(community) : "Comunidade"}</h3><p className="match-outcome">{draw ? "Empate da mesa" : winner ? `Vencedor informado: ${winner.display_name}` : "Resultado não informado"}</p><div className="participant-chips">{match.participants.map((p) => <span key={p.player_id} className={p.result === "WIN" ? "player-chip winner" : "player-chip"}>{p.result === "WIN" && <span aria-hidden="true">✦ </span>}{p.display_name}{p.is_guest ? " · convidado" : ""}</span>)}</div></div><div className="match-meta"><span className={`badge ${match.status.toLowerCase()}`}>{labels[match.status]}</span><span>{match.approximate_start_time ? `${match.approximate_start_time.slice(0, 5)} · Brasília` : "Início não informado"}</span>{match.author && <small>Por {match.author}</small>}</div></article>;
}
