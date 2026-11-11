export default function ResourceState({ loading, error, retry, empty, children }: { loading?: boolean; error?: string; retry?: () => void; empty?: string; children?: React.ReactNode }) {
  if (loading) return <div className="state-panel" role="status"><span className="loading-rune" aria-hidden="true">✦</span><h2>Abrindo os registros…</h2><p>Um instante enquanto reunimos as histórias da comunidade.</p></div>;
  if (error) return <div className="state-panel error-panel" role="alert"><h2>O caminho está temporariamente fechado.</h2><p>{error}</p>{retry && <button className="button secondary" onClick={retry}>Tentar novamente</button>}</div>;
  if (empty) return <div className="state-panel"><span className="empty-rune" aria-hidden="true">✦</span><h2>Ainda não há registros por aqui.</h2><p>{empty}</p></div>;
  return children;
}
