import { NavigatorForm } from "@/components/navigator-form";


const principles = [
  {
    number: "01",
    title: "Geprüfte Information",
    text: "Jedes Ergebnis zeigt Quelle, Prüfdatum und bestehende Unsicherheiten.",
  },
  {
    number: "02",
    title: "Klare Regeln",
    text: "Zugangsbedingungen werden nachvollziehbar geprüft – nicht von AI entschieden.",
  },
  {
    number: "03",
    title: "Menschliche Übergabe",
    text: "Bei Gefahr, Unsicherheit oder auf Wunsch übernimmt eine Fachperson.",
  },
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#start" aria-label="Vesta Startseite">
          <span className="brand-mark" aria-hidden="true">
            V
          </span>
          <span>Vesta</span>
        </a>
        <p className="pilot-label">Pilot · Bern</p>
      </header>

      <section className="hero" id="start">
        <div className="hero-copy">
          <p className="eyebrow">Berner Sozial-Lotse</p>
          <h1>Was brauchst du gerade?</h1>
          <p className="lead">
            Wir helfen dir, ein passendes Angebot zu finden. Einfach,
            verständlich und mit sichtbaren Quellen.
          </p>
          <div className="trust-note">
            <span className="trust-dot" aria-hidden="true" />
            <p>Du brauchst kein Konto. Deine Suche wird nicht als Dossier gespeichert.</p>
          </div>
        </div>

        <NavigatorForm />
      </section>

      <section className="principles" aria-labelledby="principles-title">
        <div className="section-heading">
          <p className="eyebrow">Wie Vesta arbeitet</p>
          <h2 id="principles-title">Technik, die den Zugang erleichtert.</h2>
        </div>
        <div className="principle-grid">
          {principles.map((principle) => (
            <article className="principle-card" key={principle.number}>
              <p className="principle-number">{principle.number}</p>
              <h3>{principle.title}</h3>
              <p>{principle.text}</p>
            </article>
          ))}
        </div>
      </section>

      <footer>
        <p>Vesta ersetzt keine Notfallhilfe und reserviert keine Plätze.</p>
        <p>Initialer Prototyp · Angaben noch nicht für den Feldeinsatz freigegeben</p>
      </footer>
    </main>
  );
}
