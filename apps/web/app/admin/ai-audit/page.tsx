"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { AdminNav } from "@/components/admin-nav";
import { Button } from "@/components/ui";
import {
  downloadWorkflowMarkdown,
  type WorkflowDetail,
} from "@/lib/admin-audit-export";

type WorkflowSummary = {
  workflow_id: string;
  started_at: string;
  updated_at: string;
  input_preview: string;
  event_count: number;
  ai_call_count: number;
  complete: boolean;
  has_fallback: boolean;
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

function formatDetails(details: Record<string, unknown>): string {
  return JSON.stringify(details, null, 2);
}

export default function AiAuditPage() {
  const detailHeadingRef = useRef<HTMLHeadingElement>(null);
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [selected, setSelected] = useState<WorkflowDetail | null>(null);
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
    fetchJson<{ workflows: WorkflowSummary[] }>("/api/admin/ai-audit-workflows")
      .then((data) => setWorkflows(data.workflows))
      .catch((requestError: unknown) =>
        handleRequestError(requestError, "Workflows konnten nicht geladen werden."),
      )
      .finally(() => setLoading(false));
  }, [handleRequestError]);

  useEffect(() => {
    if (selected) {
      detailHeadingRef.current?.focus();
    }
  }, [selected]);

  async function openWorkflow(workflowId: string) {
    setError(null);
    try {
      const detail = await fetchJson<WorkflowDetail>(
        `/api/admin/ai-audit-workflows/${encodeURIComponent(workflowId)}`,
      );
      setSelected(detail);
    } catch (requestError) {
      handleRequestError(requestError, "Workflow konnte nicht geladen werden.");
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
      <AdminNav />
      <div className="admin-heading">
        <div>
          <p className="eyebrow">Admin-Audit</p>
          <h1>Dialog-Workflows</h1>
        </div>
        <Button onClick={logout} variant="ghost">
          Abmelden
        </Button>
      </div>

      <p className="admin-intro">
        Jeder Workflow zeigt die nachvollziehbare Kette von der Eingabe über AI und
        deterministische Vesta-Logik bis zur sichtbaren Antwort.
      </p>

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {loading && (
        <p aria-live="polite" className="field-hint" role="status">
          Workflows werden geladen …
        </p>
      )}

      {!loading && workflows.length === 0 && (
        <p aria-live="polite" className="field-hint" role="status">
          Noch keine vollständigen Dialog-Workflows protokolliert.
        </p>
      )}

      {workflows.length > 0 && (
        <ul aria-label="Protokollierte Dialog-Workflows" className="workflow-list">
          {workflows.map((workflow) => {
            const updatedAt = formatTime(workflow.updated_at);
            return (
              <li className="workflow-card" key={workflow.workflow_id}>
                <div className="workflow-card-heading">
                  <div>
                    <time dateTime={workflow.updated_at}>{updatedAt}</time>
                    <p className="workflow-preview">{workflow.input_preview}</p>
                  </div>
                  <span
                    className={`workflow-status ${
                      workflow.complete ? "workflow-status--complete" : ""
                    }`}
                  >
                    {workflow.complete ? "Vollständige Spur" : "Teilspur"}
                  </span>
                </div>
                <p className="field-hint">
                  {workflow.event_count} Prozessschritte · {workflow.ai_call_count} AI-Aufrufe
                  {workflow.has_fallback ? " · mit Fallback" : ""}
                </p>
                <Button
                  aria-label={`Workflow vom ${updatedAt} öffnen`}
                  onClick={() => openWorkflow(workflow.workflow_id)}
                  variant="secondary"
                >
                  Workflow öffnen
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      {selected && (
        <section
          aria-labelledby="workflow-detail-heading"
          className="navigator-card workflow-detail"
        >
          <div className="workflow-detail-heading">
            <div>
              <p className="eyebrow">Ablauf</p>
              <h2 id="workflow-detail-heading" ref={detailHeadingRef} tabIndex={-1}>
                Workflow-Details
              </h2>
            </div>
            <div className="workflow-detail-actions">
              <span
                className={`workflow-status ${
                  selected.complete ? "workflow-status--complete" : ""
                }`}
              >
                {selected.complete ? "Vollständige Spur" : "Historische Teilspur"}
              </span>
              <Button
                aria-label="Vollständige Spur als Markdown-Datei herunterladen"
                onClick={() => downloadWorkflowMarkdown(selected)}
                variant="secondary"
              >
                Download (.md)
              </Button>
            </div>
          </div>
          <p className="field-hint">
            Workflow-ID: <code>{selected.workflow_id}</code>
          </p>

          <ol aria-label="Chronologischer Ablauf des Dialogs" className="workflow-timeline">
            {selected.steps.map((step, index) => (
              <li
                className={`workflow-step workflow-step--${step.kind}`}
                key={step.id}
              >
                <div aria-hidden="true" className="workflow-step-number">
                  {index + 1}
                </div>
                <article>
                  <div className="workflow-step-heading">
                    <h3>{step.label}</h3>
                    <time dateTime={step.created_at}>{formatTime(step.created_at)}</time>
                  </div>
                  <p>{step.summary}</p>
                  {step.kind === "ai" && (
                    <p className="field-hint">
                      {step.provider}/{step.model} · {step.outcome}
                    </p>
                  )}
                  <details className="workflow-technical-details">
                    <summary>Technische Details anzeigen</summary>
                    <pre className="admin-audit-text">{formatDetails(step.details)}</pre>
                  </details>
                </article>
              </li>
            ))}
          </ol>

          <Button onClick={() => setSelected(null)} variant="ghost">
            Schliessen
          </Button>
        </section>
      )}
    </main>
  );
}
