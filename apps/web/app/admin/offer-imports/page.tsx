"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";

import { AdminNav } from "@/components/admin-nav";
import { Button } from "@/components/ui";

type ImportStatus =
  | "queued"
  | "fetching"
  | "extracting"
  | "translating"
  | "ready_for_review"
  | "failed";

type ImportJob = {
  id: string;
  source_url: string;
  normalized_url: string;
  status: ImportStatus;
  requested_by: string;
  offer_id: string | null;
  source_language: string | null;
  extracted_data: Record<string, unknown> | null;
  evidence: { field: string; excerpt: string }[];
  duplicate_offer_ids: string[];
  error_code: string | null;
  error_detail: string | null;
  attempts: number;
  created_at: string;
  updated_at: string;
};

const STATUS_LABELS: Record<ImportStatus, string> = {
  queued: "Wartet",
  fetching: "Quelle wird geladen",
  extracting: "Angaben werden extrahiert",
  translating: "Übersetzungen werden erstellt",
  ready_for_review: "Bereit zur Prüfung",
  failed: "Fehlgeschlagen",
};

function formatExtracted(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Nicht belegt";
  if (Array.isArray(value)) return value.join(", ") || "Nicht belegt";
  if (typeof value === "object") return JSON.stringify(value);
  if (typeof value === "boolean") return value ? "Ja" : "Nein";
  return String(value);
}

export default function OfferImportsPage() {
  const [url, setUrl] = useState("");
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const selected = jobs.find((job) => job.id === selectedId) ?? null;

  const load = useCallback(async () => {
    const response = await fetch("/api/admin/offer-import-jobs?limit=100&offset=0", {
      cache: "no-store",
    });
    if (response.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    if (!response.ok) throw new Error("load_failed");
    setJobs(((await response.json()) as { jobs: ImportJob[] }).jobs);
  }, []);

  useEffect(() => {
    const initial = window.setTimeout(() => {
      load().catch(() => setError("Importaufträge konnten nicht geladen werden."));
    }, 0);
    const interval = window.setInterval(() => {
      load().catch(() => undefined);
    }, 3000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(interval);
    };
  }, [load]);

  async function createJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const response = await fetch("/api/admin/offer-import-jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (response.status === 401) {
        window.location.replace("/admin/login");
        return;
      }
      const payload = (await response.json()) as ImportJob & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "create_failed");
      setUrl("");
      setSelectedId(payload.id);
      setNotice("Importauftrag wurde angenommen. Der Entwurf wird nie automatisch veröffentlicht.");
      await load();
    } catch (createError) {
      const detail = createError instanceof Error ? createError.message : "create_failed";
      const messages: Record<string, string> = {
        https_required: "Bitte geben Sie eine HTTPS-Adresse ein.",
        https_port_443_required: "Es sind nur HTTPS-Adressen auf Port 443 erlaubt.",
        blocked_address: "Lokale oder private Zieladressen sind nicht erlaubt.",
      };
      setError(messages[detail] ?? "Der Importauftrag konnte nicht erstellt werden.");
    } finally {
      setSubmitting(false);
    }
  }

  async function retry(job: ImportJob) {
    setError(null);
    const response = await fetch(`/api/admin/offer-import-jobs/${job.id}/retry`, {
      method: "POST",
    });
    if (response.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    if (!response.ok) {
      setError("Dieser Auftrag kann nicht erneut gestartet werden.");
      return;
    }
    setNotice("Der Auftrag wurde erneut eingereiht.");
    await load();
  }

  return (
    <main className="admin-shell admin-import-shell" id="main-content">
      <AdminNav />
      <div className="admin-heading">
        <div><p className="eyebrow">Angebotsquellen</p><h1>URL-Import</h1></div>
      </div>
      <p className="admin-intro">
        Vesta prüft eine öffentliche HTTPS-Seite, extrahiert belegte Angaben und erstellt sechs
        Sprachentwürfe. Vor der manuellen Prüfung wird nichts veröffentlicht.
      </p>
      {error && <p className="error-message" role="alert">{error}</p>}
      {notice && <p className="admin-success" role="status">{notice}</p>}

      <section aria-labelledby="new-import-heading" className="admin-panel">
        <h2 id="new-import-heading">Neue Quelle prüfen</h2>
        <form className="admin-import-form" onSubmit={createJob}>
          <label className="field" htmlFor="offer-source-url">
            Öffentliche HTTPS-URL
            <input
              id="offer-source-url"
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://organisation.ch/angebot"
              required
              type="url"
              value={url}
            />
          </label>
          <Button disabled={submitting} type="submit">
            {submitting ? "Wird eingereiht …" : "Import starten"}
          </Button>
        </form>
      </section>

      <div className="admin-import-layout">
        <section aria-labelledby="imports-heading" className="admin-panel">
          <h2 id="imports-heading">Importaufträge</h2>
          {jobs.length === 0 ? <p>Noch keine URL-Importe.</p> : (
            <div className="admin-table-scroll" role="region" aria-label="URL-Importaufträge" tabIndex={0}>
              <table className="admin-table">
                <thead><tr><th scope="col">Quelle</th><th scope="col">Status</th><th scope="col">Versuche</th><th scope="col">Aktion</th></tr></thead>
                <tbody>{jobs.map((job) => (
                  <tr key={job.id}>
                    <td><strong>{new URL(job.normalized_url).hostname}</strong><span className="admin-offer-secondary">{new Date(job.created_at).toLocaleString("de-CH")}</span></td>
                    <td><span className={`offer-status offer-status--${job.status}`}>{STATUS_LABELS[job.status]}</span></td>
                    <td>{job.attempts}/3</td>
                    <td><Button onClick={() => setSelectedId(job.id)} variant="ghost">Details</Button></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </section>

        <section aria-labelledby="import-detail-heading" className="admin-panel">
          <h2 id="import-detail-heading">Prüfdetails</h2>
          {!selected ? <p>Wählen Sie einen Auftrag aus.</p> : (
            <div className="admin-import-detail">
              <p><strong>Status:</strong> {STATUS_LABELS[selected.status]}</p>
              <p><a href={selected.normalized_url} rel="noopener noreferrer" target="_blank">Quelle öffnen</a></p>
              {selected.error_code && <p className="error-message" role="alert"><strong>{selected.error_code}</strong><br />{selected.error_detail}</p>}
              {selected.duplicate_offer_ids.length > 0 && (
                <div className="admin-warning"><strong>Mögliche Dubletten</strong><ul>{selected.duplicate_offer_ids.map((id) => <li key={id}><code>{id}</code></li>)}</ul></div>
              )}
              {selected.extracted_data && (
                <div className="admin-evidence-grid">
                  {Object.entries(selected.extracted_data).filter(([key]) => key !== "evidence").map(([key, value]) => {
                    const evidence = selected.evidence.filter((item) => item.field === key);
                    return <article key={key}><h3>{key}</h3><p>{formatExtracted(value)}</p>{evidence.length ? <ul>{evidence.map((item, index) => <li key={`${item.field}-${index}`}>{item.excerpt}</li>)}</ul> : <p className="uncertainty">Kein eigener Quellenbeleg</p>}</article>;
                  })}
                </div>
              )}
              <div className="admin-form-actions">
                {selected.offer_id && <Button href={`/admin/offers?offer=${selected.offer_id}`} variant="secondary">Angebotsentwurf prüfen</Button>}
                {selected.status === "failed" && selected.attempts < 3 && <Button onClick={() => retry(selected)} variant="secondary">Erneut versuchen</Button>}
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
