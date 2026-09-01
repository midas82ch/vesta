"use client";

import { useCallback, useEffect, useState } from "react";

import { AdminNav } from "@/components/admin-nav";
import { Button } from "@/components/ui";

type IngestionRun = {
  id: string;
  offer_slug: string;
  source_url: string;
  status: "imported" | "evidence_missing" | "fetch_failed" | "skipped_disabled";
  http_status: number | null;
  content_sha256: string | null;
  missing_evidence: string[];
  error: string | null;
  checked_at: string;
};

const STATUS_LABELS: Record<IngestionRun["status"], string> = {
  imported: "Importiert",
  evidence_missing: "Beleg fehlt",
  fetch_failed: "Abruf fehlgeschlagen",
  skipped_disabled: "Automatik ausgeschaltet",
};

type ImportSettings = {
  automatic_enabled: boolean;
  revision: number;
  updated_at: string;
  updated_by: string | null;
};

class RequestError extends Error {
  constructor(readonly status: number) {
    super(`request_failed_${status}`);
  }
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new RequestError(response.status);
  }
  return (await response.json()) as T;
}

function formatTime(value: string): string {
  return new Date(value).toLocaleString("de-CH");
}

export default function IngestionRunsPage() {
  const [runs, setRuns] = useState<IngestionRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<ImportSettings | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const handleRequestError = useCallback((requestError: unknown, message: string) => {
    if (requestError instanceof RequestError && requestError.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    setError(message);
  }, []);

  useEffect(() => {
    Promise.all([
      fetchJson<{ runs: IngestionRun[] }>("/api/admin/ingestion-runs"),
      fetchJson<ImportSettings>("/api/admin/import-settings"),
    ])
      .then(([data, importSettings]) => {
        setRuns(data.runs);
        setSettings(importSettings);
      })
      .catch((requestError: unknown) =>
        handleRequestError(requestError, "Prüfläufe konnten nicht geladen werden."),
      )
      .finally(() => setLoading(false));
  }, [handleRequestError]);

  async function logout() {
    const response = await fetch("/api/admin/logout", { method: "POST" });
    if (response.ok) {
      window.location.replace("/admin/login");
      return;
    }
    setError("Abmeldung derzeit nicht möglich.");
  }

  async function toggleAutomaticImport() {
    if (!settings) return;
    setSavingSettings(true);
    setError(null);
    setNotice(null);
    try {
      const response = await fetch("/api/admin/import-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          automatic_enabled: !settings.automatic_enabled,
          revision: settings.revision,
        }),
      });
      if (response.status === 401) {
        window.location.replace("/admin/login");
        return;
      }
      if (!response.ok) throw new RequestError(response.status);
      const updated = (await response.json()) as ImportSettings;
      setSettings(updated);
      setNotice(
        updated.automatic_enabled
          ? "Die automatische Angebotsprüfung ist wieder aktiv."
          : "Die automatische Angebotsprüfung ist ausgeschaltet. Bestehende Angebote bleiben unverändert.",
      );
    } catch (requestError) {
      handleRequestError(
        requestError,
        "Import-Einstellung konnte nicht gespeichert werden.",
      );
    } finally {
      setSavingSettings(false);
    }
  }

  return (
    <main className="admin-shell">
      <AdminNav />
      <div className="admin-heading">
        <div>
          <p className="eyebrow">Admin-Audit</p>
          <h1>Angebots-Prüfung</h1>
        </div>
        <Button onClick={logout} variant="ghost">
          Abmelden
        </Button>
      </div>

      <p className="admin-intro">
        Die tägliche automatische Prüfung gleicht jede Angebotsquelle gegen die
        hinterlegten Bestätigungssätze ab und aktualisiert die Datenbank. Diese Liste
        zeigt die letzten Prüfläufe.
      </p>

      {settings && (
        <section aria-labelledby="import-control-heading" className="admin-import-control">
          <div>
            <p className="eyebrow">Betriebssteuerung</p>
            <h2 id="import-control-heading">Automatische Angebotsprüfung</h2>
            <p>
              Status: <strong>{settings.automatic_enabled ? "Aktiv" : "Ausgeschaltet"}</strong>
              {settings.updated_by && (
                <> · zuletzt geändert von {settings.updated_by} am {formatTime(settings.updated_at)}</>
              )}
            </p>
            <p className="field-hint">
              Das Ausschalten verhindert neue automatische Läufe. Ein bereits laufender
              Prüflauf wird beendet; veröffentlichte und manuelle Angebote bleiben bestehen.
            </p>
          </div>
          <Button
            disabled={savingSettings}
            onClick={toggleAutomaticImport}
            variant={settings.automatic_enabled ? "ghost" : "secondary"}
          >
            {savingSettings
              ? "Wird gespeichert …"
              : settings.automatic_enabled
                ? "Automatik ausschalten"
                : "Automatik einschalten"}
          </Button>
        </section>
      )}

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {notice && <p className="admin-success" role="status">{notice}</p>}
      {loading && (
        <p aria-live="polite" className="field-hint" role="status">
          Prüfläufe werden geladen …
        </p>
      )}

      {!loading && runs.length === 0 && (
        <p aria-live="polite" className="field-hint" role="status">
          Noch keine Prüfläufe protokolliert.
        </p>
      )}

      {runs.length > 0 && (
        <div
          aria-label="Prüfläufe, horizontal scrollbar"
          className="admin-table-scroll"
          role="region"
          tabIndex={0}
        >
          <table className="admin-table">
            <thead>
              <tr>
                <th scope="col">Zeitpunkt</th>
                <th scope="col">Angebot</th>
                <th scope="col">Status</th>
                <th scope="col">HTTP</th>
                <th scope="col">Fehlende Belege</th>
                <th scope="col">Fehler</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td>{formatTime(run.checked_at)}</td>
                  <td>
                    <a href={run.source_url} rel="noreferrer" target="_blank">
                      {run.offer_slug}
                    </a>
                  </td>
                  <td>
                    <span className={`ingestion-status ingestion-status--${run.status}`}>
                      {STATUS_LABELS[run.status]}
                    </span>
                  </td>
                  <td>{run.http_status ?? "–"}</td>
                  <td>
                    {run.missing_evidence.length > 0 ? run.missing_evidence.join(", ") : "–"}
                  </td>
                  <td>{run.error ?? "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
