import BrandHeader from "../components/BrandHeader";

export default function HomePage() {
  return (
    <>
      <BrandHeader />
      <section
        aria-labelledby="encounters-heading"
        className="mt-12 rounded-2xl border border-stone-800 bg-stone-900 p-6 sm:p-8"
      >
        <h2 id="encounters-heading" className="text-xl font-semibold">
          Seu próximo encontro começa aqui.
        </h2>
        <p className="mt-3 leading-relaxed text-stone-300">
          Um espaço para registrar partidas, construir seu histórico e
          acompanhar sua comunidade.
        </p>
      </section>
    </>
  );
}
