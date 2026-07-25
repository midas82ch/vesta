"use client";

import { FormEvent, useState } from "react";


type Need = "sleep_tonight" | "basic_needs" | "counselling";

type Candidate = {
  offer: {
    id: string;
    name: string;
    summary: string;
    availability: "confirmed" | "call_to_confirm" | "unknown";
    contact_note: string;
    is_demo: boolean;
    source: {
      label: string;
      url: string | null;
      verified_at: string;
      expires_at: string;
      verified_by: string;
    };
  };
  reasons: string[];
  uncertainties: string[];
};

type MatchResponse = {
  candidates: Candidate[];
  human_handoff_required: boolean;
  handoff_reason: string | null;
  disclaimer: string;
};

const needs: Array<{ value: Need; title: string; detail: string; icon: string }> = [
  {
    value: "sleep_tonight",
    title: "Heute schlafen",
    detail: "Einen Platz für die Nacht suchen",
    icon: "⌂",
  },
  {
    value: "basic_needs",
    title: "Grundversorgung",
    detail: "Essen, Dusche oder Ersthilfe",
    icon: "＋",
  },
  {
    value: "counselling",
    title: "Beratung",
    detail: "Hilfe bei Sucht, Wohnen oder Geld",
    icon: "→",
  },
];

const availabilityLabels = {
  confirmed: "Status bestätigt",
  call_to_confirm: "Bitte vorher abklären",
  unknown: "Status unbekannt",
};

export function NavigatorForm() {
  const [selectedNeed, setSelectedNeed] = useState<Need>("sleep_tonight");
  const [language, setLanguage] = useState("de");
  const [targetGroup, setTargetGroup] = useState("");
  const [dog, setDog] = useState(false);
  const [hasIdentityDocument, setHasIdentityDocument] = useState(true);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    "idle",
  );
  const [result, setResult] = useState<MatchResponse | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("loading");
    setResult(null);

    try {
      const response = await fetch("/api/matches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          need: selectedNeed,
          language,
          gender: targetGroup || null,
          dog,
          has_identity_document: hasIdentityDocument,
          risk_flags: [],
        }),
      });

      if (!response.ok) {
        throw new Error("request_failed");
      }

      setResult((await response.json()) as MatchResponse);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="navigator-card">
      <form onSubmit={submit}>
        <fieldset>
          <legend>Wähle einen Bereich</legend>
          <div className="need-options">
            {needs.map((need) => (
              <label
                className={`need-option ${
                  selectedNeed === need.value ? "need-option-selected" : ""
                }`}
                key={need.value}
              >
                <input
                  checked={selectedNeed === need.value}
                  name="need"
                  onChange={() => setSelectedNeed(need.value)}
                  type="radio"
                  value={need.value}
                />
                <span className="need-icon" aria-hidden="true">
                  {need.icon}
                </span>
                <span>
                  <strong>{need.title}</strong>
                  <small>{need.detail}</small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="form-row">
          <label className="select-label">
            Sprache
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option value="de">Deutsch</option>
              <option value="fr">Français</option>
              <option value="en">English</option>
              <option value="ar">العربية</option>
            </select>
          </label>
          <label className="select-label">
            Zielgruppe
            <select
              value={targetGroup}
              onChange={(event) => setTargetGroup(event.target.value)}
            >
              <option value="">Keine Angabe</option>
              <option value="finta">Frau / FINTA</option>
              <option value="other">Andere / allgemeine Suche</option>
            </select>
          </label>
          <div className="check-group">
            <label>
              <input
                checked={dog}
                onChange={(event) => setDog(event.target.checked)}
                type="checkbox"
              />
              Ich habe einen Hund
            </label>
            <label>
              <input
                checked={!hasIdentityDocument}
                onChange={(event) => setHasIdentityDocument(!event.target.checked)}
                type="checkbox"
              />
              Ich habe keinen Ausweis
            </label>
          </div>
        </div>

        <button className="primary-button" disabled={status === "loading"} type="submit">
          {status === "loading" ? "Angebote werden geprüft …" : "Passende Hilfe finden"}
          <span aria-hidden="true">→</span>
        </button>
      </form>

      <div aria-live="polite" className="result-region">
        {status === "error" && (
          <p className="error-message">
            Die Suche ist gerade nicht erreichbar. Bitte versuche es später erneut oder
            wende dich direkt an eine Fachperson.
          </p>
        )}

        {status === "success" && result && (
          <div className="results">
            <div className="result-heading">
              <p className="eyebrow">Ergebnis</p>
              <h2>
                {result.candidates.length === 1
                  ? "Ein mögliches Angebot"
                  : `${result.candidates.length} mögliche Angebote`}
              </h2>
            </div>

            {result.candidates.map((candidate) => (
              <article className="result-card" key={candidate.offer.id}>
                {candidate.offer.is_demo && (
                  <p className="demo-badge">Testdaten · nicht für den Feldeinsatz</p>
                )}
                <h3>{candidate.offer.name}</h3>
                <p>{candidate.offer.summary}</p>
                <p className="availability">
                  {availabilityLabels[candidate.offer.availability]}
                </p>
                {candidate.uncertainties.length > 0 && (
                  <p className="uncertainty">Einzelne Angaben müssen abgeklärt werden.</p>
                )}
                <p className="contact-note">{candidate.offer.contact_note}</p>
                <p className="source">
                  Automatisch geprüft{" "}
                  {new Intl.DateTimeFormat("de-CH").format(
                    new Date(candidate.offer.source.verified_at),
                  )}{" "}
                  · Quelle:{" "}
                  {candidate.offer.source.url ? (
                    <a
                      href={candidate.offer.source.url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {candidate.offer.source.label}
                    </a>
                  ) : (
                    candidate.offer.source.label
                  )}
                </p>
              </article>
            ))}

            {result.human_handoff_required && (
              <p className="handoff-message">
                Wir haben kein verlässlich passendes Angebot gefunden. Eine Fachperson
                sollte die Situation übernehmen.
              </p>
            )}
            <p className="disclaimer">{result.disclaimer}</p>
          </div>
        )}
      </div>
    </div>
  );
}
