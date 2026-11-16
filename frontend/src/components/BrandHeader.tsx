export function Crest({ small = false }: { small?: boolean }) {
  return <svg className={small ? "crest small" : "crest"} viewBox="0 0 48 56" fill="none" aria-hidden="true"><path d="M3 4 24 1l21 3v27c0 12-21 23-21 23S3 43 3 31V4Z" stroke="currentColor" strokeWidth="1.5"/><path d="m24 10 3 11 11 3-11 3-3 11-3-11-11-3 11-3 3-11Z" fill="currentColor"/><path d="M14 44h20" stroke="currentColor"/></svg>;
}
export default function BrandHeader() {
  return <a className="brand" href="#/" aria-label="Scroll of Encounters — início"><Crest small/><span>SCROLL <em>of</em><br/>ENCOUNTERS<small>A crônica da sua mesa</small></span></a>;
}
