import { useState } from "react";
import type { FormEvent } from "react";
import { useApp } from "../state/AppContext";
import { api } from "../services/api";
import { errorMessage } from "../hooks/useResource";
import type { Player, Registration } from "../types";
import { communityName } from "../types";
import ResourceState from "../components/ResourceState";

function today() {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
  return ["year", "month", "day"].map((type) => parts.find((p) => p.type === type)?.value).join("-");
}
export default function RegisterMatchPage() {
  const { catalog, user, authLoading } = useApp();
  const [community, setCommunity] = useState("");
  const [format, setFormat] = useState("");
  const [date, setDate] = useState(today);
  const [start, setStart] = useState("");
  const [participants, setParticipants] = useState<number[]>([]);
  const [search, setSearch] = useState("");
  const [extraPlayers, setExtraPlayers] = useState<Player[]>([]);
  const [guestName, setGuestName] = useState("");
  const [guestBusy, setGuestBusy] = useState(false);
  const [kind, setKind] = useState("winner");
  const [winner, setWinner] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Registration>();
  const selectedFormat = catalog.data?.formats.find((f) => String(f.id) === format);
  const players = [...new Map([...(catalog.data?.players || []), ...extraPlayers].map((p) => [p.id, p])).values()];
  const selected = players.filter((p) => participants.includes(p.id));
  const atMaximum = selectedFormat?.max_players != null && participants.length >= selectedFormat.max_players;
  function toggle(id: number) {
    setParticipants((previous) => previous.includes(id) ? previous.filter((value) => value !== id) : [...previous, id]);
    if (winner === String(id)) setWinner("");
  }
  async function addGuest() {
    setGuestBusy(true); setError("");
    try {
      const player = await api.request<Player>("/players/guests", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ display_name: guestName, community_id: Number(community) }) });
      if (player) { setExtraPlayers((previous) => [...previous, player]); setParticipants((previous) => [...previous, player.id]); setGuestName(""); catalog.reload(); }
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setGuestBusy(false); }
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    if (!selectedFormat || participants.length < selectedFormat.min_players || (selectedFormat.max_players != null && participants.length > selectedFormat.max_players)) {
      setError("Confira a quantidade de participantes permitida pelo formato."); return;
    }
    setBusy(true);
    try {
      const saved = await api.request<Registration>("/matches", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ community_id: Number(community), format_id: Number(format), match_date: date, approximate_start_time: start, participant_ids: participants, result: kind === "draw" ? { type: "draw" } : { type: "winner", winner_player_id: Number(winner) } }) });
      if (saved) { setResult(saved); catalog.reload(); }
    } catch (failure) { setError(errorMessage(failure)); }
    finally { setBusy(false); }
  }
  if (authLoading) return <ResourceState loading/>;
  if (!user) return <div className="login-prompt"><span className="empty-rune">✦</span><div className="eyebrow">ASSINE SUA CRÔNICA</div><h1>Seu encontro merece<br/>uma autoria de verdade.</h1><p>Entre na sua conta para registrar partidas.<br/>Seus convidados também têm lugar à mesa.</p><a href="#/entrar" className="button primary">Entrar e registrar →</a><a href="#/historico" className="text-link">Explorar o histórico</a></div>;
  if (user.needs_profile) return <div className="state-panel"><h1>Sua identidade vem primeiro.</h1><p>Escolha seu nome público e comunidade principal para assinar os registros.</p><a href="#/perfil" className="button primary">Completar perfil</a></div>;
  if (result) return <div className="success-card"><span className="success-seal">✦</span><div className="eyebrow">UM NOVO CAPÍTULO FOI GUARDADO</div><h1>Partida #{result.id}<br/>registrada.</h1><span className="badge pending">Aguardando validação</span><p>Seu relato já faz parte do histórico. Ele só contará nas estatísticas oficiais depois de verificado.</p>{result.warnings.map((warning) => <div key={warning.code} className="notice" role="status">{warning.message}{warning.match_ids?.length ? ` Partidas: ${warning.match_ids.join(", ")}.` : ""}</div>)}<div className="hero-actions"><a className="button primary" href="#/historico">Ver o histórico →</a><button className="button secondary" onClick={() => { setResult(undefined); setStart(""); setError(""); }}>Registrar outro encontro</button></div></div>;
  return <><div className="eyebrow">ESCREVA UMA NOVA CRÔNICA</div><div className="section-title"><div><h1>Registrar partida</h1><p>Um registro simples. Uma história que permanece.</p></div><span className="badge guest">Assinado por {user.username}</span></div><ResourceState loading={catalog.loading && !catalog.data} error={catalog.error} retry={catalog.reload}><form className="registration-layout" onSubmit={(event) => { void submit(event); }}><div className="form-sections"><section className="form-card"><div className="form-section-title"><span>01</span><div><h2>Onde e quando</h2><p>A comunidade anfitriã e o início aproximado do encontro.</p></div></div><div className="field-grid"><label><span>Comunidade anfitriã</span><select value={community} required onChange={(event) => setCommunity(event.target.value)}><option value="">Selecione uma comunidade</option>{catalog.data?.communities.map((c) => <option key={c.id} value={c.id}>{communityName(c)} · {c.city}/{c.state_code}</option>)}</select></label><label><span>Formato</span><select value={format} required onChange={(event) => setFormat(event.target.value)}><option value="">Selecione um formato</option>{catalog.data?.formats.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}</select></label><label><span>Data da partida</span><input type="date" required value={date} onChange={(event) => setDate(event.target.value)}/></label><label><span>Início aproximado · Brasília</span><input type="time" required value={start} onChange={(event) => setStart(event.target.value)}/></label></div><p className="form-note">Partidas de qualquer data são bem-vindas. Informe o início que você recorda; não usamos término ou duração.</p></section>
    <section className="form-card"><div className="form-section-title"><span>02</span><div><h2>Quem estava à mesa</h2><p>Selecione jogadores de qualquer comunidade, incluindo convidados.</p></div></div><div className="roster-summary">{participants.length} selecionados {selectedFormat && <span>· Mínimo {selectedFormat.min_players}{selectedFormat.max_players != null ? ` · Máximo ${selectedFormat.max_players}` : " · Sem máximo definido"}</span>}</div><label><span>Buscar participante</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nome ou apelido"/></label><div className="roster">{players.filter((p) => p.display_name.toLocaleLowerCase().includes(search.toLocaleLowerCase())).map((p) => <label className={`roster-player ${participants.includes(p.id) ? "selected" : ""}`} key={p.id}><input type="checkbox" checked={participants.includes(p.id)} disabled={Boolean(!participants.includes(p.id) && atMaximum)} onChange={() => toggle(p.id)}/><span className="roster-initial">{p.display_name[0]}</span><span><strong>{p.display_name}</strong><small>{p.is_guest ? "Convidado persistente" : "Jogador registrado"} · #{p.id}</small></span></label>)}{players.filter((p) => p.display_name.toLocaleLowerCase().includes(search.toLocaleLowerCase())).length === 0 && <p className="form-note">Nenhum participante encontrado. Confira o nome ou cadastre um convidado.</p>}</div><details className="guest-details"><summary>+ Alguém ainda não tem uma identidade…</summary><p className="form-note">Confira a lista antes de criar. O convidado ficará disponível para os próximos encontros. Use um apelido para distinguir homônimos.</p><label><span>Nome do novo convidado</span><input value={guestName} onChange={(event) => setGuestName(event.target.value)} minLength={2} maxLength={80} placeholder="Nome ou apelido conhecido"/></label><button type="button" className="button secondary" disabled={!community || guestName.trim().length < 2 || guestBusy || busy || Boolean(atMaximum)} onClick={() => { void addGuest(); }}>{guestBusy ? "Criando identidade…" : "Criar e adicionar convidado"}</button>{!community && <small>Selecione a comunidade anfitriã primeiro.</small>}</details></section>
    <section className="form-card"><div className="form-section-title"><span>03</span><div><h2>Como terminou</h2><p>Informe um vencedor ou o empate de toda a mesa.</p></div></div><div className="result-options"><label className={kind === "winner" ? "result-option selected" : "result-option"}><input type="radio" name="result" value="winner" checked={kind === "winner"} onChange={() => setKind("winner")}/><span>✦</span><strong>Um vencedor</strong></label><label className={kind === "draw" ? "result-option selected" : "result-option"}><input type="radio" name="result" value="draw" checked={kind === "draw"} onChange={() => { setKind("draw"); setWinner(""); }}/><span>✦</span><strong>Empate da mesa</strong></label></div>{kind === "winner" && <label><span>Quem venceu?</span><select required value={winner} onChange={(event) => setWinner(event.target.value)}><option value="">Selecione um participante</option>{selected.map((p) => <option key={p.id} value={p.id}>{p.display_name}</option>)}</select></label>}</section>{error && <div role="alert" className="inline-error">{error}</div>}<button className="button primary full" disabled={busy || guestBusy || !catalog.data}>{busy ? "Guardando sua história…" : "Registrar partida"}<span aria-hidden="true">✦</span></button></div>
    <aside className="registration-note"><div className="eyebrow">UM RELATO DE CONFIANÇA</div><h2>A mesa muda.<br/>A história fica.</h2><span className="ornament">✦ ─── ✦</span><ul><li>Seu registro começa pendente de validação.</li><li>Não há limite de partidas por dia.</li><li>Um participante não pode iniciar outra partida a menos de 10 minutos desta. Exatamente 10 minutos é permitido.</li><li>Avisos de possível duplicidade ajudam a conferir o histórico.</li></ul><p>Somente partidas verificadas entram nas estatísticas oficiais.</p></aside></form></ResourceState></>;
}
