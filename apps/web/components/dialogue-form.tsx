"use client";

import { type FormEvent, useState } from "react";

import { useI18n } from "@/components/i18n-provider";
import type { MessageKey } from "@/lib/i18n";
import { needs, type Need } from "@/lib/needs";

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

type EntryMode = "pick" | "other";
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

function titleFor(needValue: string): MessageKey {
  return (needs.find((need) => need.value === needValue)?.title ??
    "need.sleep.title") as MessageKey;
}

export function DialogueForm() {
  const { locale, t } = useI18n();
  const [entryMode, setEntryMode] = useState<EntryMode>("pick");
  const [freeText, setFreeText] = useState("");
  const [interpretation, setInterpretation] = useState<InterpretResponse | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [turn, setTurn] = useState<DialogueTurn | null>(null);
  const [numberValue, setNumberValue] = useState("");

  const busy = phase === "interpreting" || phase === "loading";
  const onEntryScreen = phase !== "question" && phase !== "result";

  async function startWithNeed(need: Need) {
    setPhase("loading");
    try {
      const result = await postJson<DialogueTurn>("/api/dialogue/start", {
        need,
        language: locale,
      });
      applyTurn(result);
    } catch {
      setPhase("error");
    }
  }

  async function handleInterpret(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPhase("interpreting");
    try {
      const result = await postJson<InterpretResponse>("/api/dialogue/interpret", {
        free_text: freeText,
        language: locale,
      });
      setInterpretation(result);
      setPhase("idle");
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

  function backToPicker() {
    setEntryMode("pick");
    setInterpretation(null);
    setFreeText("");
  }

  function restart() {
    setTurn(null);
    backToPicker();
    setPhase("idle");
  }

  return (
    <div className="navigator-card">
      {onEntryScreen && entryMode === "pick" && (
        <fieldset>
          <legend>{t("dialogue.needPicker.legend")}</legend>
          <div className="need-options">
            {needs.map((need) => (
              <button
                className="need-option"
                disabled={busy}
                key={need.value}
                onClick={() => startWithNeed(need.value)}
                type="button"
              >
                <span className="need-icon" aria-hidden="true">
                  {need.icon}
                </span>
                <span className="need-copy">
                  <strong>{t(need.title)}</strong>
                  <small>{t(need.detail)}</small>
                </span>
                <span aria-hidden="true">→</span>
              </button>
            ))}
            <button
              className="need-option"
              disabled={busy}
              onClick={() => setEntryMode("other")}
              type="button"
            >
              <span className="need-icon" aria-hidden="true">
                ?
              </span>
              <span className="need-copy">
                <strong>{t("dialogue.other.title")}</strong>
                <small>{t("dialogue.other.detail")}</small>
              </span>
              <span aria-hidden="true">→</span>
            </button>
          </div>
          {phase === "loading" && <p className="field-hint">{t("dialogue.loading")}</p>}
        </fieldset>
      )}

      {onEntryScreen && entryMode === "other" && (
        <>
          <p className="eyebrow">{t("dialogue.eyebrow")}</p>

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
              {phase === "interpreting"
                ? t("dialogue.freeText.loading")
                : t("dialogue.freeText.submit")}
            </button>
          </form>

          {interpretation && !interpretation.need_key && (
            <p className="field-hint">{t("dialogue.interpretation.unavailable")}</p>
          )}

          {interpretation && (
            <div className="need-options">
              {interpretation.need_key && (
                <button
                  className="need-option need-option-selected"
                  disabled={busy}
                  onClick={() => startWithNeed(interpretation.need_key as Need)}
                  type="button"
                >
                  <span className="need-icon" aria-hidden="true">
                    ✓
                  </span>
                  <span className="need-copy">
                    <strong>
                      {t("dialogue.interpretation.needApplied", {
                        need: t(titleFor(interpretation.need_key)),
                      })}
                    </strong>
                    <small>{t("dialogue.interpretation.confirmHint")}</small>
                  </span>
                  <span aria-hidden="true">→</span>
                </button>
              )}

              {!interpretation.need_key &&
                needs.map((need) => (
                  <button
                    className="need-option"
                    disabled={busy}
                    key={need.value}
                    onClick={() => startWithNeed(need.value)}
                    type="button"
                  >
                    <span className="need-icon" aria-hidden="true">
                      {need.icon}
                    </span>
                    <span className="need-copy">
                      <strong>{t(need.title)}</strong>
                      <small>{t(need.detail)}</small>
                    </span>
                    <span aria-hidden="true">→</span>
                  </button>
                ))}
            </div>
          )}

          <button disabled={busy} onClick={backToPicker} type="button">
            {t("dialogue.back")}
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
            {turn.ai_mode === "live" ? t("dialogue.aiBadge") : t("dialogue.templateBadge")}
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

          <button disabled={busy} onClick={() => submitAnswer({ unknown: true })} type="button">
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
