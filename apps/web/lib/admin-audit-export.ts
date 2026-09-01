export type WorkflowStep = {
  id: string;
  kind: "input" | "ai" | "system" | "output";
  event_type: string;
  label: string;
  summary: string;
  created_at: string;
  provider: string | null;
  model: string | null;
  outcome: string | null;
  details: Record<string, unknown>;
};

export type WorkflowDetail = {
  workflow_id: string;
  started_at: string;
  updated_at: string;
  complete: boolean;
  steps: WorkflowStep[];
};

function fencedBlock(value: string, language = "text"): string {
  const backtickRuns = value.match(/`+/g) ?? [];
  const longestRun = backtickRuns.reduce(
    (longest, run) => Math.max(longest, run.length),
    0,
  );
  const fence = "`".repeat(Math.max(3, longestRun + 1));
  return `${fence}${language}\n${value}\n${fence}`;
}

function optionalValue(value: string | null): string {
  return value ?? "—";
}

export function workflowToMarkdown(workflow: WorkflowDetail): string {
  const lines = [
    "# Vesta AI-Audit – Dialog-Workflow",
    "",
    "## Workflow-Metadaten",
    "",
    `- Status: ${workflow.complete ? "Vollständige Spur" : "Historische Teilspur"}`,
    `- Beginn: ${workflow.started_at}`,
    `- Letzte Aktualisierung: ${workflow.updated_at}`,
    `- Prozessschritte: ${workflow.steps.length}`,
    "",
    "### Workflow-ID",
    "",
    fencedBlock(workflow.workflow_id),
    "",
    "## Vollständige Spur",
    "",
  ];

  workflow.steps.forEach((step, index) => {
    lines.push(
      `### ${index + 1}. ${step.label}`,
      "",
      `- Schritt-ID: ${step.id}`,
      `- Art: ${step.kind}`,
      `- Ereignis: ${step.event_type}`,
      `- Zeitpunkt: ${step.created_at}`,
      `- Provider: ${optionalValue(step.provider)}`,
      `- Modell: ${optionalValue(step.model)}`,
      `- Ergebnis: ${optionalValue(step.outcome)}`,
      "",
      "#### Zusammenfassung",
      "",
      fencedBlock(step.summary),
      "",
      "#### Sämtliche technische Daten",
      "",
      fencedBlock(JSON.stringify(step.details, null, 2), "json"),
      "",
    );
  });

  lines.push(
    "## Vollständige Rohdaten",
    "",
    "Dieser Abschnitt enthält das vollständige, unveränderte Detailobjekt des Dialogs.",
    "",
    fencedBlock(JSON.stringify(workflow, null, 2), "json"),
    "",
  );

  return `${lines.join("\n").trimEnd()}\n`;
}

export function workflowExportFilename(workflowId: string): string {
  const safeId = workflowId
    .normalize("NFKD")
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100);
  return `vesta-ai-audit-${safeId || "workflow"}.md`;
}

export function downloadWorkflowMarkdown(workflow: WorkflowDetail): void {
  const blob = new Blob(["\uFEFF", workflowToMarkdown(workflow)], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = workflowExportFilename(workflow.workflow_id);
  link.hidden = true;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
