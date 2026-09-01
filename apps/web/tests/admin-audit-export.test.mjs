import assert from "node:assert/strict";
import test from "node:test";

import {
  workflowExportFilename,
  workflowToMarkdown,
} from "../lib/admin-audit-export.ts";

const workflow = {
  workflow_id: "dialog/ä",
  started_at: "2026-09-01T10:00:00Z",
  updated_at: "2026-09-01T10:01:00Z",
  complete: true,
  steps: [
    {
      id: "step-1",
      kind: "ai",
      event_type: "interpret",
      label: "AI · Eingabe verstehen",
      summary: "Darija: شنو ```",
      created_at: "2026-09-01T10:00:30Z",
      provider: "openai",
      model: "test-model",
      outcome: "ai",
      details: {
        request_text: "vollständiger Prompt",
        response_text: "جواب",
      },
    },
  ],
};

test("exports a readable trace and the complete raw workflow", () => {
  const markdown = workflowToMarkdown(workflow);

  assert.match(markdown, /^# Vesta AI-Audit – Dialog-Workflow/m);
  assert.match(markdown, /## Vollständige Spur/);
  assert.match(markdown, /Darija: شنو ```/);
  assert.match(markdown, /````text/);
  assert.match(markdown, /## Vollständige Rohdaten/);
  assert.match(markdown, /"request_text": "vollständiger Prompt"/);
  assert.match(markdown, /"response_text": "جواب"/);
  assert.equal(markdown.endsWith("\n"), true);
});

test("creates a safe Markdown filename from the workflow ID", () => {
  assert.equal(
    workflowExportFilename(workflow.workflow_id),
    "vesta-ai-audit-dialog-a.md",
  );
  assert.equal(workflowExportFilename("///"), "vesta-ai-audit-workflow.md");
});
