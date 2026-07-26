"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui";

type AuditSummary = {
  id: string;
  session_id: string | null;
  port: string;
  provider: string;
  model: string;
  outcome: string;
  created_at: string;
};

type AuditDetail = AuditSummary & {
  violations: string[];
  error_detail: string | null;
  request_text: string;
  response_text: string | null;
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

export default function AiAuditPage() {
  const detailHeadingRef = useRef<HTMLHeadingElement>(null);
  const [entries, setEntries] = useState<AuditSummary[]>([]);
  const [selected, setSelected] = useState<AuditDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleRequestError = useCallback((requestError: unknown, message: string) => {
    if (requestError instanceof RequestError && requestError.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    setError(message);
  }, []);

  useEffect(() => {
    fetchJson<{ entries: AuditSummary[] }>("/api/admin/ai-audit-log")
      .then((data) => setEntries(data.entries))
      .catch((requestError: unknown) =>
        handleRequestError(requestError, "Liste konnte nicht geladen werden."),
      )
      .finally(() => setLoading(false));
  }, [handleRequestError]);

  useEffect(() => {
    if (selected) {
      detailHeadingRef.current?.focus();
    }
  }, [selected]);

  async function openEntry(id: string) {
    setError(null);
    try {
      const detail = await fetchJson<AuditDetail>(`/api/admin/ai-audit-log/${id}`);
      setSelected(detail);
    } catch (requestError) {
      handleRequestError(requestError, "Eintrag konnte nicht geladen werden.");
    }
  }

  async function logout() {
    const response = await fetch("/api/admin/logout", { method: "POST" });
    if (response.ok) {
      window.location.replace("/admin/login");
      return;
    }
    setError("Abmeldung derzeit nicht möglich.");
  }

  return (
    <main className="admin-shell">
      <div className="admin-heading">
        <h1>AI-Audit-Log</h1>
        <Button onClick={logout} variant="ghost">
          Abmelden
        </Button>
      </div>

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {loading && (
        <p aria-live="polite" className="field-hint" role="status">
          Wird geladen …
        </p>
      )}

      {!loading && entries.length === 0 && (
        <p aria-live="polite" className="field-hint" role="status">
          Noch keine KI-Interaktionen protokolliert.
        </p>
      )}

      {entries.length > 0 && (
        <div
          aria-label="AI-Audit-Einträge, horizontal scrollbar"
          className="admin-table-scroll"
          role="region"
          tabIndex={0}
        >
          <table className="admin-table">
            <thead>
              <tr>
                <th scope="col">Zeitpunkt</th>
                <th scope="col">Port</th>
                <th scope="col">Provider/Modell</th>
                <th scope="col">Ergebnis</th>
                <th scope="col">Session</th>
                <th scope="col">
                  <span className="visually-hidden">Aktion</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => {
                const createdAt = new Date(entry.created_at).toLocaleString("de-CH");
                return (
                  <tr key={entry.id}>
                    <td>{createdAt}</td>
                    <td>{entry.port}</td>
                    <td>
                      {entry.provider} / {entry.model}
                    </td>
                    <td>{entry.outcome}</td>
                    <td>{entry.session_id ?? "–"}</td>
                    <td>
                      <Button
                        aria-label={`Details für Audit-Eintrag vom ${createdAt} anzeigen`}
                        onClick={() => openEntry(entry.id)}
                        variant="secondary"
                      >
                        Details
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <section aria-labelledby="audit-detail-heading" className="navigator-card admin-detail">
          <p className="field-hint">
            {selected.port} · {selected.provider}/{selected.model} · {selected.outcome}
          </p>
          <h2 id="audit-detail-heading" ref={detailHeadingRef} tabIndex={-1}>
            Audit-Details
          </h2>
          {selected.violations.length > 0 && (
            <p className="field-hint">Verstösse: {selected.violations.join(", ")}</p>
          )}
          {selected.error_detail && (
            <p className="error-message" role="alert">
              {selected.error_detail}
            </p>
          )}
          <h3>Anfrage</h3>
          <pre className="admin-audit-text">{selected.request_text}</pre>
          <h3>Antwort</h3>
          <pre className="admin-audit-text">
            {selected.response_text ?? "(keine Antwort erhalten)"}
          </pre>
          <Button onClick={() => setSelected(null)} variant="ghost">
            Schliessen
          </Button>
        </section>
      )}
    </main>
  );
}
