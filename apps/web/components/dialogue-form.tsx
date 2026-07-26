"use client";

import { type FormEvent, useState } from "react";

import { useI18n } from "@/components/i18n-provider";
import { Button, ChoiceList, NumberField, TextAreaField, type ChoiceOption } from "@/components/ui";
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
type AnswerType = "yes_no_unknown" | "single_choice" | "number";

type RenderedQuestion = {
  question_key: string;
  attribute_key: string;
  answer_type: AnswerType;
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

const OTHER_NEED_VALUE = "__other__";

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

  function handleNeedPick(value: string) {
    if (value === OTHER_NEED_VALUE) {
      setEntryMode("other");
      return;
    }
    startWithNeed(value as Need);
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

  const needPickerOptions: ChoiceOption[] = [
    ...needs.map((need) => ({
      value: need.value,
      icon: need.icon,
      label: t(need.title),
      detail: t(need.detail),
    })),
    {
      value: OTHER_NEED_VALUE,
      icon: "?",
      label: t("dialogue.other.title"),
      detail: t("dialogue.other.detail"),
    },
  ];

  const interpretationOptions: ChoiceOption[] = interpretation?.need_key
    ? [
        {
          value: interpretation.need_key,
          icon: "✓",
          label: t("dialogue.interpretation.needApplied", {
            need: t(titleFor(interpretation.need_key)),
          }),
          detail: t("dialogue.interpretation.confirmHint"),
        },
      ]
    : needs.map((need) => ({
        value: need.value,
        icon: need.icon,
        label: t(need.title),
        detail: t(need.detail),
      }));

  return (
    <div className="navigator-card">
      {onEntryScreen && entryMode === "pick" && (
        <fieldset>
          <legend>{t("dialogue.needPicker.legend")}</legend>
          <ChoiceList disabled={busy} onSelect={handleNeedPick} options={needPickerOptions} />
          {phase === "loading" && <p className="field-hint">{t("dialogue.loading")}</p>}
        </fieldset>
      )}

      {onEntryScreen && entryMode === "other" && (
        <>
          <p className="eyebrow">{t("dialogue.eyebrow")}</p>

          <form onSubmit={handleInterpret}>
            <TextAreaField
              hint={t("dialogue.freeText.privacy")}
              id="dialogue-free-text"
              label={t("dialogue.freeText.label")}
              maxLength={2000}
              onChange={(event) => setFreeText(event.target.value)}
              placeholder={t("dialogue.freeText.placeholder")}
              rows={3}
              value={freeText}
            />
            <Button disabled={busy} type="submit">
              {phase === "interpreting"
                ? t("dialogue.freeText.loading")
                : t("dialogue.freeText.submit")}
            </Button>
          </form>

          {interpretation && !interpretation.need_key && (
            <p className="field-hint">{t("dialogue.interpretation.unavailable")}</p>
          )}

          {interpretation && (
            <ChoiceList
              disabled={busy}
              onSelect={(value) => startWithNeed(value as Need)}
              options={interpretationOptions}
              selectedValue={interpretation.need_key ?? undefined}
            />
          )}

          <Button disabled={busy} onClick={backToPicker} variant="ghost">
            {t("dialogue.back")}
          </Button>
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

          {turn.question.answer_type === "single_choice" && (
            <ChoiceList
              disabled={busy}
              onSelect={(value) => submitAnswer({ value })}
              options={turn.question.options.map((option) => ({
                value: option.value,
                label: option.label,
              }))}
            />
          )}

          {turn.question.answer_type === "yes_no_unknown" && (
            <ChoiceList
              disabled={busy}
              onSelect={(value) => submitAnswer({ value: value === "yes" })}
              options={[
                { value: "yes", label: t("dialogue.question.yes") },
                { value: "no", label: t("dialogue.question.no") },
              ]}
            />
          )}

          {turn.question.answer_type === "number" && (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                if (numberValue.trim() !== "") {
                  submitAnswer({ value: Number(numberValue) });
                }
              }}
            >
              <NumberField
                id="dialogue-number-answer"
                label={t("dialogue.question.numberSubmit")}
                onChange={(event) => setNumberValue(event.target.value)}
                value={numberValue}
              />
              <Button disabled={busy} type="submit">
                {t("dialogue.question.numberSubmit")}
              </Button>
            </form>
          )}

          <div className="btn-group">
            <Button
              disabled={busy}
              onClick={() => submitAnswer({ unknown: true })}
              variant="ghost"
            >
              {turn.question.unknown_label}
            </Button>
            <Button
              disabled={busy}
              onClick={() => submitAnswer({ declined: true })}
              variant="ghost"
            >
              {turn.question.decline_label}
            </Button>
          </div>
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
        <div className="form-footer">
          <Button onClick={restart} variant="ghost">
            {t("dialogue.restart")}
          </Button>
        </div>
      )}
    </div>
  );
}
