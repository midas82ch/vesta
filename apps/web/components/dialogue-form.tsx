"use client";

import { type FormEvent, useState } from "react";

import { useI18n } from "@/components/i18n-provider";
import { needs, type Need } from "@/components/navigator-form";
import type { MessageKey } from "@/lib/i18n";

type Offer = {
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

type ExplanationReason = { text: string; supported_by: string[] };

type Explanation = {
  headline: string;
  reasons: ExplanationReason[];
  clarification: ExplanationReason | null;
  next_action: string | null;
  source: "ai" | "template";
};

type ExplainedCandidate = {
  candidate: { offer: Offer; reasons: string[]; uncertainties: string[] };
  explanation: Explanation | null;
};

type QuestionOption = { value: string; label: string };

type RenderedQuestion = {
  question_key: string;
  attribute_key: string;
  text: string;
  help_text: string | null;
  unknown_label: string;
  decline_label: string;
  options: QuestionOption[];
  source: "ai" | "template";
};

type DialogueTurn = {
  session_id: string;
  ai_mode: "live" | "template";
  question: RenderedQuestion | null;
  candidates: ExplainedCandidate[];
  human_handoff_required: boolean;
  handoff_reason: string | null;
  disclaimer: string;
};

type InterpretResponse = {
  need_key: string | null;
  proposals: { key: string; value: unknown; confidence: string }[];
  requires_confirmation: string[];
  ambiguities: string[];
  source: "ai" | "template";
};

type Phase = "idle" | "interpreting" | "loading" | "question" | "result" | "error";

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`request_failed_${response.status}`);
  }
  return (await response.json()) as T;
}

export function DialogueForm() {
  const { locale, t } = useI18n();
  const [freeText, setFreeText] = useState("");
  const [selectedNeed, setSelectedNeed] = useState<Need>("sleep_tonight");
  const [interpretation, setInterpretation] = useState<InterpretResponse | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [turn, setTurn] = useState<DialogueTurn | null>(null);
  const [numberValue, setNumberValue] = useState("");

  async function handleInterpret(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPhase("interpreting");
    try {
      const result = await postJson<InterpretResponse>("/api/dialogue/interpret", {
        free_text: freeText,
        language: locale,
      });
      setInterpretation(result);
      if (result.need_key) {
        setSelectedNeed(result.need_key as Need);
      }
      setPhase("idle");
    } catch {
      setPhase("error");
    }
  }

  async function handleStart() {
    setPhase("loading");
    try {
      const result = await postJson<DialogueTurn>("/api/dialogue/start", {
        need: selectedNeed,
        language: locale,
      });
      applyTurn(result);
    } catch {
      setPhase("error");
    }
  }

  function applyTurn(result: DialogueTurn) {
    setTurn(result);
    setNumberValue("");
    setPhase(result.question ? "question" : "result");
  }

  async function submitAnswer(
    body: { value?: unknown; unknown?: boolean; declined?: boolean },
  ) {
    if (!turn?.question) return;
    setPhase("loading");
    try {
      const result = await postJson<DialogueTurn>("/api/dialogue/answer", {
        session_id: turn.session_id,
        question_key: turn.question.question_key,
        ...body,
      });
      applyTurn(result);
    } catch {
      setPhase("error");
    }
  }

  function restart() {
    setTurn(null);
    setInterpretation(null);
    setFreeText("");
    setPhase("idle");
  }

  const busy = phase === "interpreting" || phase === "loading";

  return (
    <div className="navigator-card dialogue-card">
      <p className="eyebrow">{t("dialogue.eyebrow")}</p>

      {phase !== "question" && phase !== "result" && (
        <>
          <form onSubmit={handleInterpret}>
            <label className="select-label" htmlFor="dialogue-free-text">
              {t("dialogue.freeText.label")}
              <textarea
                aria-describedby="dialogue-free-text-privacy"
                id="dialogue-free-text"
                maxLength={2000}
                placeholder={t("dialogue.freeText.placeholder")}
                value={freeText}
                onChange={(event) => setFreeText(event.target.value)}
                rows={3}
              />
            </label>
            <p className="field-hint" id="dialogue-free-text-privacy">
              {t("dialogue.freeText.privacy")}
            </p>
            <button className="primary-button" disabled={busy} type="submit">
              {phase === "interpreting" ? t("dialogue.freeText.loading") : t("dialogue.freeText.submit")}
            </button>
          </form>

          {interpretation && interpretation.proposals.length === 0 && (
            <p className="field-hint">{t("dialogue.interpretation.unavailable")}</p>
          )}
          {interpretation?.need_key && (
            <p className="field-hint">
              {t("dialogue.interpretation.needApplied", {
                need: t(
                  (needs.find((n) => n.value === interpretation.need_key)?.title ??
                    "need.sleep.title") as MessageKey,
                ),
              })}
            </p>
          )}

          <fieldset>
            <legend>{t("dialogue.needPicker.legend")}</legend>
            <div className="need-options">
              {needs.map((need) => (
                <label
                  className={`need-option ${
                    selectedNeed === need.value ? "need-option-selected" : ""
                  }`}
                  key={need.value}
                >
                  <span className="need-icon" aria-hidden="true">
                    {need.icon}
                  </span>
                  <span className="need-copy">
                    <strong>{t(need.title)}</strong>
                    <small>{t(need.detail)}</small>
                  </span>
                  <input
                    checked={selectedNeed === need.value}
                    name="dialogue-need"
                    onChange={() => setSelectedNeed(need.value)}
                    type="radio"
                    value={need.value}
                  />
                </label>
              ))}
            </div>
          </fieldset>

          <button
            className="primary-button"
            disabled={busy}
            onClick={handleStart}
            type="button"
          >
            {phase === "loading" ? t("dialogue.loading") : t("dialogue.start")}
          </button>
        </>
      )}

      {phase === "error" && <p className="error-message">{t("dialogue.error")}</p>}

      {phase === "question" && turn?.question && (
        <div className="results">
          <p className="eyebrow">{t("dialogue.question.eyebrow")}</p>
          <h3>{turn.question.text}</h3>
          {turn.question.help_text && <p>{turn.question.help_text}</p>}
          <p className="field-hint">
            {turn.ai_mode === "live"
              ? t("dialogue.aiBadge")
              : t("dialogue.templateBadge")}
          </p>

          <div className="need-options">
            {turn.question.options.length > 0
              ? turn.question.options.map((option) => (
                  <button
                    className="primary-button"
                    disabled={busy}
                    key={option.value}
                    onClick={() => submitAnswer({ value: option.value })}
                    type="button"
                  >
                    {option.label}
                  </button>
                ))
              : (
                  <>
                    <button
                      className="primary-button"
                      disabled={busy}
                      onClick={() => submitAnswer({ value: true })}
                      type="button"
                    >
                      {t("dialogue.question.yes")}
                    </button>
                    <button
                      className="primary-button"
                      disabled={busy}
                      onClick={() => submitAnswer({ value: false })}
                      type="button"
                    >
                      {t("dialogue.question.no")}
                    </button>
                  </>
                )}
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (numberValue.trim() !== "") {
                submitAnswer({ value: Number(numberValue) });
              }
            }}
          >
            <label className="select-label" htmlFor="dialogue-number-answer">
              {t("dialogue.question.numberSubmit")}
              <input
                id="dialogue-number-answer"
                inputMode="numeric"
                onChange={(event) => setNumberValue(event.target.value)}
                type="number"
                value={numberValue}
              />
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              {t("dialogue.question.numberSubmit")}
            </button>
          </form>

          <button
            disabled={busy}
            onClick={() => submitAnswer({ unknown: true })}
            type="button"
          >
            {turn.question.unknown_label}
          </button>
          <button
            disabled={busy}
            onClick={() => submitAnswer({ declined: true })}
            type="button"
          >
            {turn.question.decline_label}
          </button>
        </div>
      )}

      {phase === "result" && turn && (
        <div className="results">
          <div className="result-heading">
            <p className="eyebrow">{t("dialogue.result.eyebrow")}</p>
          </div>

          {turn.candidates.map(({ candidate, explanation }) => (
            <article className="result-card" key={candidate.offer.id}>
              {candidate.offer.is_demo && (
                <p className="demo-badge">{t("results.demoBadge")}</p>
              )}
              <div lang="de">
                <h3>{candidate.offer.name}</h3>
              </div>
              {explanation ? (
                <>
                  <p className="field-hint">
                    {explanation.source === "ai"
                      ? t("dialogue.aiBadge")
                      : t("dialogue.templateBadge")}
                  </p>
                  <p lang={explanation.source === "ai" ? locale : "de"}>
                    {explanation.headline}
                  </p>
                  <ul>
                    {explanation.reasons.map((reason) => (
                      <li key={reason.text}>{reason.text}</li>
                    ))}
                  </ul>
                  {explanation.clarification && (
                    <p className="uncertainty">{explanation.clarification.text}</p>
                  )}
                </>
              ) : (
                <p>{candidate.offer.summary}</p>
              )}
              <p className="contact-note" lang="de">
                {candidate.offer.contact_note}
              </p>
              <p className="source">
                {t("results.source")}:{" "}
                <span lang="de">{candidate.offer.source.label}</span>
              </p>
            </article>
          ))}

          {turn.human_handoff_required && (
            <p className="handoff-message">{t("results.handoff")}</p>
          )}
          <p className="disclaimer">{turn.disclaimer}</p>
        </div>
      )}

      {(phase === "question" || phase === "result") && (
        <button onClick={restart} type="button">
          {t("dialogue.restart")}
        </button>
      )}
    </div>
  );
}
