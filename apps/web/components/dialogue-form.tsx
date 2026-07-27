"use client";

import {
  type FormEvent,
  type Ref,
  useEffect,
  useRef,
  useState,
} from "react";

import { useI18n } from "@/components/i18n-provider";
import { NeedSymbol } from "@/components/need-symbol";
import { Button, ChoiceList, NumberField, TextAreaField, type ChoiceOption } from "@/components/ui";
import { localeTags, type Locale, type MessageKey } from "@/lib/i18n";
import { needs, type Need } from "@/lib/needs";

type Offer = {
  id: string;
  name: string;
  summary: string;
  availability: "confirmed" | "call_to_confirm" | "unknown";
  contact_note: string;
  address: string | null;
  directions_url: string | null;
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
  candidate: {
    offer: Offer;
    reasons: string[];
    uncertainties: string[];
    distance_meters: number | null;
  };
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
  workflow_id: string;
  need_key: string | null;
  proposals: { key: string; value: unknown; confidence: string }[];
  requires_confirmation: string[];
  ambiguities: string[];
  source: "ai" | "template";
};

type EntryMode = "pick" | "other";
type Phase = "idle" | "interpreting" | "loading" | "question" | "result" | "error";
type UserLocation = { latitude: number; longitude: number };
type LocationStatus =
  | "idle"
  | "locating"
  | "active"
  | "denied"
  | "timeout"
  | "unavailable";
type ConversationMessage = {
  id: string;
  speaker: "person" | "vesta";
  text: string;
};

const OTHER_NEED_VALUE = "__other__";
const UNKNOWN_ANSWER_VALUE = "__unknown__";
const DECLINED_ANSWER_VALUE = "__declined__";

function formatDistance(
  meters: number,
  locale: Locale,
  t: (key: MessageKey, values?: Record<string, string | number>) => string,
) {
  if (meters < 1_000) {
    const roundedMeters = Math.max(50, Math.round(meters / 50) * 50);
    return t("results.distance.meters", {
      distance: new Intl.NumberFormat(localeTags[locale]).format(roundedMeters),
    });
  }

  const kilometers = meters / 1_000;
  return t("results.distance.kilometers", {
    distance: new Intl.NumberFormat(localeTags[locale], {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(kilometers),
  });
}

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

function symbolFor(needValue: string) {
  return needs.find((need) => need.value === needValue)?.icon ?? "other";
}

function DialogueProgress({ currentStage }: { currentStage: number }) {
  const { t } = useI18n();
  const steps: MessageKey[] = [
    "dialogue.progress.need",
    "dialogue.progress.questions",
    "dialogue.progress.results",
  ];

  return (
    <nav aria-label={t("dialogue.progress.label")} className="dialogue-progress">
      <ol>
        {steps.map((label, index) => {
          const current = index === currentStage;
          const complete = index < currentStage;
          return (
            <li
              aria-current={current ? "step" : undefined}
              className={
                current
                  ? "dialogue-progress-step dialogue-progress-step--current"
                  : complete
                    ? "dialogue-progress-step dialogue-progress-step--complete"
                    : "dialogue-progress-step"
              }
              key={label}
            >
              <span aria-hidden="true" className="dialogue-progress-number">
                {complete ? "✓" : index + 1}
              </span>
              <span>{t(label)}</span>
              <span className="visually-hidden">
                {current
                  ? `, ${t("dialogue.progress.current")}`
                  : complete
                    ? `, ${t("dialogue.progress.complete")}`
                    : ""}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function ConversationThread({
  activeQuestionId,
  headingRef,
  messages,
}: {
  activeQuestionId?: string | null;
  headingRef?: Ref<HTMLHeadingElement>;
  messages: ConversationMessage[];
}) {
  const { t } = useI18n();

  return (
    <div
      aria-label={t("dialogue.conversation.label")}
      className="dialogue-conversation"
    >
      {messages.map((message) => {
        const activeQuestion =
          message.speaker === "vesta" && message.id === activeQuestionId;
        return (
          <article
            className={`dialogue-message dialogue-message--${message.speaker}`}
            key={message.id}
          >
            <p className="dialogue-speaker">
              {message.speaker === "person"
                ? t("dialogue.conversation.you")
                : t("dialogue.conversation.vesta")}
            </p>
            {activeQuestion ? (
              <h3 ref={headingRef} tabIndex={-1}>
                {message.text}
              </h3>
            ) : (
              <p>{message.text}</p>
            )}
          </article>
        );
      })}
    </div>
  );
}

function BusyDialogue({
  body,
  messages,
  title,
}: {
  body: string;
  messages: ConversationMessage[];
  title: string;
}) {
  const { t } = useI18n();

  return (
    <section className="dialogue-busy">
      <ConversationThread messages={messages} />
      <article
        aria-atomic="true"
        aria-live="polite"
        className="dialogue-message dialogue-message--vesta dialogue-message--pending"
        role="status"
      >
        <div aria-hidden="true" className="dialogue-thinking">
          <span />
          <span />
          <span />
        </div>
        <div>
          <p className="dialogue-speaker">{t("dialogue.conversation.vesta")}</p>
          <h3>{title}</h3>
          <p>{body}</p>
        </div>
      </article>
    </section>
  );
}

function LocationControl({
  onRemove,
  onUse,
  status,
}: {
  onRemove: () => void;
  onUse: () => void;
  status: LocationStatus;
}) {
  const { t } = useI18n();
  const statusKey: MessageKey | null =
    status === "locating"
      ? "dialogue.location.locating"
      : status === "active"
        ? "dialogue.location.active"
        : status === "denied"
          ? "dialogue.location.denied"
          : status === "timeout"
            ? "dialogue.location.timeout"
            : status === "unavailable"
              ? "dialogue.location.unavailable"
              : null;

  return (
    <section
      aria-labelledby="dialogue-location-title"
      className="dialogue-location"
    >
      <div>
        <h2 id="dialogue-location-title">{t("dialogue.location.title")}</h2>
        <p>{t("dialogue.location.text")}</p>
      </div>
      <div className="dialogue-location-actions">
        {status === "active" ? (
          <Button onClick={onRemove} variant="ghost">
            {t("dialogue.location.remove")}
          </Button>
        ) : (
          <Button
            disabled={status === "locating"}
            onClick={onUse}
            variant="secondary"
          >
            {status === "locating"
              ? t("dialogue.location.locating")
              : t("dialogue.location.use")}
          </Button>
        )}
      </div>
      {statusKey && (
        <p
          aria-atomic="true"
          aria-live="polite"
          className={`dialogue-location-status dialogue-location-status--${status}`}
          role="status"
        >
          {t(statusKey)}
        </p>
      )}
    </section>
  );
}

export function DialogueForm() {
  const { locale, t } = useI18n();
  const messageCounter = useRef(0);
  const responseHeadingRef = useRef<HTMLHeadingElement>(null);
  const [entryMode, setEntryMode] = useState<EntryMode>("pick");
  const [freeText, setFreeText] = useState("");
  const [interpretation, setInterpretation] = useState<InterpretResponse | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [turn, setTurn] = useState<DialogueTurn | null>(null);
  const [numberValue, setNumberValue] = useState("");
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const [locationStatus, setLocationStatus] =
    useState<LocationStatus>("idle");

  const busy = phase === "interpreting" || phase === "loading";
  const locationBusy = locationStatus === "locating";
  const onEntryScreen = phase === "idle";
  const currentStage =
    phase === "result"
      ? 2
      : phase === "question" || phase === "loading" || (phase === "error" && turn)
        ? 1
        : 0;

  useEffect(() => {
    if (phase === "question" || phase === "result" || phase === "error") {
      responseHeadingRef.current?.focus();
    }
  }, [phase]);

  function createMessage(
    speaker: ConversationMessage["speaker"],
    text: string,
  ): ConversationMessage {
    messageCounter.current += 1;
    return {
      id: `dialogue-message-${messageCounter.current}`,
      speaker,
      text,
    };
  }

  function appendMessage(
    speaker: ConversationMessage["speaker"],
    text: string,
  ) {
    const message = createMessage(speaker, text);
    setConversation((current) => [...current, message]);
    return message;
  }

  function requestLocation() {
    if (!navigator.geolocation) {
      setUserLocation(null);
      setLocationStatus("unavailable");
      return;
    }

    setLocationStatus("locating");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude: Number(position.coords.latitude.toFixed(3)),
          longitude: Number(position.coords.longitude.toFixed(3)),
        });
        setLocationStatus("active");
      },
      (error) => {
        setUserLocation(null);
        if (error.code === error.PERMISSION_DENIED) {
          setLocationStatus("denied");
        } else if (error.code === error.TIMEOUT) {
          setLocationStatus("timeout");
        } else {
          setLocationStatus("unavailable");
        }
      },
      {
        enableHighAccuracy: false,
        maximumAge: 300_000,
        timeout: 8_000,
      },
    );
  }

  function removeLocation() {
    setUserLocation(null);
    setLocationStatus("idle");
  }

  async function startWithNeed(need: Need, workflowId?: string) {
    appendMessage(
      "person",
      t("dialogue.conversation.selectedNeed", {
        need: t(titleFor(need)),
      }),
    );
    setActiveQuestionId(null);
    setPhase("loading");
    try {
      const result = await postJson<DialogueTurn>("/api/dialogue/start", {
        need,
        language: locale,
        workflow_id: workflowId,
        ...(userLocation ? { user_location: userLocation } : {}),
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
    const submittedText = freeText.trim();
    if (!submittedText) return;
    setInterpretation(null);
    setConversation([createMessage("person", submittedText)]);
    setActiveQuestionId(null);
    setPhase("interpreting");
    try {
      const result = await postJson<InterpretResponse>("/api/dialogue/interpret", {
        free_text: submittedText,
        language: locale,
      });
      setInterpretation(result);
      appendMessage(
        "vesta",
        result.need_key
          ? t("dialogue.conversation.interpreted", {
              need: t(titleFor(result.need_key)),
            })
          : t("dialogue.interpretation.unclear"),
      );
      setPhase("idle");
    } catch {
      setPhase("error");
    }
  }

  function applyTurn(result: DialogueTurn) {
    setTurn(result);
    setNumberValue("");
    const responseMessage = appendMessage(
      "vesta",
      result.question?.text ?? t("dialogue.conversation.resultsReady"),
    );
    setActiveQuestionId(result.question ? responseMessage.id : null);
    setPhase(result.question ? "question" : "result");
  }

  async function submitAnswer(
    body: { value?: unknown; unknown?: boolean; declined?: boolean },
    visibleAnswer: string,
  ) {
    if (!turn?.question) return;
    appendMessage(
      "person",
      t("dialogue.conversation.answer", { answer: visibleAnswer }),
    );
    setActiveQuestionId(null);
    setPhase("loading");
    try {
      const result = await postJson<DialogueTurn>("/api/dialogue/answer", {
        session_id: turn.session_id,
        question_key: turn.question.question_key,
        ...(userLocation ? { user_location: userLocation } : {}),
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
    setConversation([]);
    setActiveQuestionId(null);
  }

  function restart() {
    setTurn(null);
    backToPicker();
    setPhase("idle");
  }

  function skipOptions(question: RenderedQuestion): ChoiceOption[] {
    return [
      { value: UNKNOWN_ANSWER_VALUE, label: question.unknown_label },
      { value: DECLINED_ANSWER_VALUE, label: question.decline_label },
    ];
  }

  function handleAnswerSelect(value: string) {
    if (value === UNKNOWN_ANSWER_VALUE) {
      submitAnswer({ unknown: true }, turn?.question?.unknown_label ?? value);
      return;
    }
    if (value === DECLINED_ANSWER_VALUE) {
      submitAnswer({ declined: true }, turn?.question?.decline_label ?? value);
      return;
    }
    if (turn?.question?.answer_type === "yes_no_unknown") {
      submitAnswer(
        { value: value === "yes" },
        value === "yes"
          ? t("dialogue.question.yes")
          : t("dialogue.question.no"),
      );
      return;
    }
    const selectedOption = turn?.question?.options.find(
      (option) => option.value === value,
    );
    submitAnswer({ value }, selectedOption?.label ?? value);
  }

  const needPickerOptions: ChoiceOption[] = [
    ...needs.map((need) => ({
      value: need.value,
      icon: <NeedSymbol name={need.icon} />,
      label: t(need.title),
      detail: t(need.detail),
    })),
    {
      value: OTHER_NEED_VALUE,
      icon: <NeedSymbol name="other" />,
      label: t("dialogue.other.title"),
      detail: t("dialogue.other.detail"),
    },
  ];

  const interpretationOptions: ChoiceOption[] = interpretation?.need_key
    ? [
        {
          value: interpretation.need_key,
          icon: <NeedSymbol name={symbolFor(interpretation.need_key)} />,
          label: t(titleFor(interpretation.need_key)),
          detail: t("dialogue.interpretation.confirmHint"),
        },
      ]
    : needs.map((need) => ({
        value: need.value,
        icon: <NeedSymbol name={need.icon} />,
        label: t(need.title),
        detail: t(need.detail),
      }));

  const busyTitle =
    phase === "interpreting"
      ? t("dialogue.busy.interpreting.title")
      : turn
        ? t("dialogue.busy.answer.title")
        : t("dialogue.busy.starting.title");
  const busyBody =
    phase === "interpreting"
      ? t("dialogue.busy.interpreting.text")
      : turn
        ? t("dialogue.busy.answer.text")
        : t("dialogue.busy.starting.text");

  return (
    <div aria-busy={busy || locationBusy} className="navigator-card">
      {conversation.length > 0 && <DialogueProgress currentStage={currentStage} />}

      {!busy && onEntryScreen && (
        <LocationControl
          onRemove={removeLocation}
          onUse={requestLocation}
          status={locationStatus}
        />
      )}

      {busy && (
        <BusyDialogue
          body={busyBody}
          messages={conversation}
          title={busyTitle}
        />
      )}

      {!busy && onEntryScreen && entryMode === "pick" && (
        <fieldset className="need-picker" disabled={locationBusy}>
          <legend>{t("dialogue.needPicker.legend")}</legend>
          <ChoiceList
            disabled={locationBusy}
            onSelect={handleNeedPick}
            options={needPickerOptions}
          />
        </fieldset>
      )}

      {!busy && onEntryScreen && entryMode === "other" && (
        <>
          {!interpretation ? (
            <>
              <form onSubmit={handleInterpret}>
                <TextAreaField
                  id="dialogue-free-text"
                  label={t("dialogue.freeText.label")}
                  maxLength={2000}
                  disabled={locationBusy}
                  onChange={(event) => setFreeText(event.target.value)}
                  placeholder={t("dialogue.freeText.placeholder")}
                  required
                  rows={3}
                  value={freeText}
                />
                <Button disabled={locationBusy} type="submit">
                  {t("dialogue.freeText.submit")}
                </Button>
              </form>
            </>
          ) : (
            <section
              aria-labelledby="dialogue-confirmation-heading"
              className="dialogue-confirmation"
            >
              <ConversationThread messages={conversation} />
              <fieldset>
                <legend id="dialogue-confirmation-heading">
                  {t("dialogue.interpretation.confirmLegend")}
                </legend>
                <ChoiceList
                  disabled={locationBusy}
                  onSelect={(value) =>
                    startWithNeed(value as Need, interpretation.workflow_id)
                  }
                  options={interpretationOptions}
                  selectedValue={interpretation.need_key ?? undefined}
                />
              </fieldset>
            </section>
          )}

          <Button disabled={locationBusy} onClick={backToPicker} variant="ghost">
            {t("dialogue.back")}
          </Button>
        </>
      )}

      {!busy && phase === "error" && (
        <section
          aria-labelledby="dialogue-error-heading"
          className="dialogue-error"
        >
          {conversation.length > 0 && (
            <ConversationThread messages={conversation} />
          )}
          <h2
            id="dialogue-error-heading"
            ref={responseHeadingRef}
            tabIndex={-1}
          >
            {t("dialogue.error.title")}
          </h2>
          <p className="error-message" role="alert">
            {t("dialogue.error")}
          </p>
        </section>
      )}

      {!busy && phase === "question" && turn?.question && (
        <section
          aria-label={t("dialogue.question.eyebrow")}
          className="results dialogue-question"
        >
          <ConversationThread
            activeQuestionId={activeQuestionId}
            headingRef={responseHeadingRef}
            messages={conversation}
          />
          {turn.question.help_text && (
            <p className="dialogue-question-help">{turn.question.help_text}</p>
          )}
          <fieldset className="dialogue-answer">
            <legend>{t("dialogue.question.answerLegend")}</legend>
            {turn.question.answer_type === "single_choice" && (
              <ChoiceList
                onSelect={handleAnswerSelect}
                options={[
                  ...turn.question.options.map((option) => ({
                    value: option.value,
                    label: option.label,
                  })),
                  ...skipOptions(turn.question),
                ]}
              />
            )}

            {turn.question.answer_type === "yes_no_unknown" && (
              <ChoiceList
                onSelect={handleAnswerSelect}
                options={[
                  { value: "yes", label: t("dialogue.question.yes") },
                  { value: "no", label: t("dialogue.question.no") },
                  ...skipOptions(turn.question),
                ]}
              />
            )}

            {turn.question.answer_type === "number" && (
              <>
                <form
                  onSubmit={(event) => {
                    event.preventDefault();
                    if (numberValue.trim() !== "") {
                      submitAnswer(
                        { value: Number(numberValue) },
                        numberValue.trim(),
                      );
                    }
                  }}
                >
                  <NumberField
                    id="dialogue-number-answer"
                    label={t("dialogue.question.numberLabel")}
                    onChange={(event) => setNumberValue(event.target.value)}
                    value={numberValue}
                  />
                  <Button type="submit">
                    {t("dialogue.question.numberSubmit")}
                  </Button>
                </form>
                <ChoiceList
                  onSelect={handleAnswerSelect}
                  options={skipOptions(turn.question)}
                />
              </>
            )}
          </fieldset>
        </section>
      )}

      {!busy && phase === "result" && turn && (
        <section
          aria-labelledby="dialogue-result-heading"
          className="results"
        >
          <ConversationThread messages={conversation} />
          <div className="result-heading">
            <p className="eyebrow">{t("dialogue.result.eyebrow")}</p>
            <h2
              id="dialogue-result-heading"
              ref={responseHeadingRef}
              tabIndex={-1}
            >
              {t("dialogue.result.title")}
            </h2>
          </div>

          {turn.candidates.map(({ candidate, explanation }) => (
            <article className="result-card" key={candidate.offer.id}>
              {candidate.offer.is_demo && (
                <p className="demo-badge">{t("results.demoBadge")}</p>
              )}
              <div lang="de">
                <h3>{candidate.offer.name}</h3>
              </div>
              {(candidate.distance_meters !== null ||
                candidate.offer.address ||
                candidate.offer.directions_url) && (
                <div className="result-location">
                  {candidate.distance_meters !== null && (
                    <p className="result-distance">
                      {formatDistance(candidate.distance_meters, locale, t)}
                    </p>
                  )}
                  {candidate.offer.address && (
                    <address lang="de">
                      <strong>{t("results.address")}:</strong>{" "}
                      {candidate.offer.address}
                    </address>
                  )}
                  {candidate.offer.directions_url && (
                    <a
                      className="directions-link"
                      href={candidate.offer.directions_url}
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                      {t("results.directions")}
                      <span className="visually-hidden">
                        {" "}
                        ({t("a11y.opensNewTab")})
                      </span>
                    </a>
                  )}
                </div>
              )}
              {explanation ? (
                <>
                  <p lang={explanation.source === "ai" ? locale : "de"}>
                    {explanation.headline}
                  </p>
                  <ul>
                    {explanation.reasons.map((reason) => (
                      <li key={reason.text}>{reason.text}</li>
                    ))}
                  </ul>
                  {explanation.clarification && (
                    <p className="uncertainty">
                      {explanation.clarification.text}
                    </p>
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
        </section>
      )}

      {(phase === "question" || phase === "result" || phase === "error") && (
        <div className="form-footer">
          <Button onClick={restart} variant="ghost">
            {t("dialogue.restart")}
          </Button>
        </div>
      )}
    </div>
  );
}
