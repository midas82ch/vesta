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
import { Button, ChoiceList, TextAreaField, type ChoiceOption } from "@/components/ui";
import { localeTags, type Locale, type MessageKey } from "@/lib/i18n";
import { needs, type Need, type NeedIcon } from "@/lib/needs";

type Offer = {
  id: string;
  name: string;
  summary: string;
  availability: "confirmed" | "call_to_confirm" | "unknown";
  contact_note: string;
  address: string | null;
  directions_url: string | null;
  is_demo: boolean;
  content_language: string;
  localization_fallback: boolean;
  source: {
    label: string;
    url: string | null;
    verified_at: string;
    expires_at: string;
    verified_by: string;
  };
};

type ExplainedCandidate = {
  candidate: {
    offer: Offer;
    reasons: string[];
    uncertainties: string[];
    distance_meters: number | null;
  };
  explanation: null;
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
  outcome: "question" | "matches" | "no_match" | "handoff";
  question: RenderedQuestion | null;
  candidates: ExplainedCandidate[];
  human_handoff_required: boolean;
  handoff_reason: string | null;
  handoff_resources: HandoffResource[];
  disclaimer: string;
};

type HandoffResource = {
  kind: "emergency" | "victim_support";
  name: string;
  phone: string;
  url: string;
  description: string;
};

type PublicCategory = {
  key: string;
  title: string;
  description: string;
  icon: NeedIcon;
};

type InterpretResponse = {
  workflow_id: string;
  need_key: string | null;
  proposals: { key: string; value: unknown; confidence: string }[];
  requires_confirmation: string[];
  ambiguities: string[];
  service_topics?: string[];
  source: "ai" | "template" | "deterministic_safety";
  outcome: "interpreted" | "safety";
  safety_turn: DialogueTurn | null;
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
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const [locationStatus, setLocationStatus] =
    useState<LocationStatus>("idle");
  const [catalogCategories, setCatalogCategories] = useState<PublicCategory[]>([]);

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

  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/categories?language=${encodeURIComponent(locale)}`, {
      cache: "no-store",
      signal: controller.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error("category_catalog_unavailable");
        return response.json() as Promise<{ categories: PublicCategory[] }>;
      })
      .then((payload) => setCatalogCategories(payload.categories))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setCatalogCategories([]);
        }
      });
    return () => controller.abort();
  }, [locale]);

  const availableCategories: PublicCategory[] = catalogCategories.length
    ? catalogCategories
    : needs.map((need) => ({
        key: need.value,
        title: t(need.title),
        description: t(need.detail),
        icon: need.icon,
      }));

  function categoryFor(value: string) {
    return availableCategories.find((category) => category.key === value);
  }

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

  async function startWithNeed(
    need: Need,
    workflowId?: string,
    serviceTopics: string[] = [],
  ) {
    appendMessage(
      "person",
      t("dialogue.conversation.selectedNeed", {
        need: categoryFor(need)?.title ?? need,
      }),
    );
    setActiveQuestionId(null);
    setPhase("loading");
    try {
      const result = await postJson<DialogueTurn>("/api/dialogue/start", {
        need,
        language: locale,
        workflow_id: workflowId,
        ...(serviceTopics.length > 0 ? { service_topics: serviceTopics } : {}),
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
      if (result.outcome === "safety" && result.safety_turn) {
        setInterpretation(null);
        appendMessage("vesta", t("dialogue.safety.detected"));
        applyTurn(result.safety_turn);
        return;
      }
      setInterpretation(result);
      appendMessage(
        "vesta",
        result.need_key
          ? t("dialogue.conversation.interpreted", {
              need: categoryFor(result.need_key)?.title ?? result.need_key,
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
    const responseMessage = appendMessage(
      "vesta",
      result.question
        ? controlledQuestionText(result.question)
        : result.outcome === "no_match"
          ? t("dialogue.conversation.noMatch")
          : result.handoff_reason === "immediate_danger"
            ? t("dialogue.safety.immediate")
            : result.handoff_reason === "victim_support_recommended"
              ? t("dialogue.safety.support")
          : t("dialogue.conversation.resultsReady"),
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
    if (
      question.attribute_key === "person.gender"
    ) {
      return [
        {
          value: DECLINED_ANSWER_VALUE,
          label: t("dialogue.fit.decline"),
        },
      ];
    }

    return [
      { value: UNKNOWN_ANSWER_VALUE, label: question.unknown_label },
      { value: DECLINED_ANSWER_VALUE, label: question.decline_label },
    ];
  }

  function controlledQuestionText(question: RenderedQuestion) {
    if (question.attribute_key === "person.gender") {
      return t("dialogue.fit.gender.question");
    }
    if (question.attribute_key === "person.is_adult") {
      return t("dialogue.fit.age.question");
    }
    return question.text;
  }

  function controlledQuestionHelp(question: RenderedQuestion) {
    if (question.attribute_key === "person.gender") {
      return t("dialogue.fit.gender.help");
    }
    if (question.attribute_key === "person.is_adult") {
      return t("dialogue.fit.age.help");
    }
    return question.help_text;
  }

  function controlledQuestionOptions(
    question: RenderedQuestion,
  ): ChoiceOption[] | null {
    if (question.attribute_key === "person.gender") {
      return [
        { value: "finta", label: t("dialogue.fit.gender.yes") },
        { value: "other", label: t("dialogue.fit.gender.no") },
      ];
    }
    if (question.attribute_key === "person.is_adult") {
      return [
        { value: "yes", label: t("dialogue.fit.age.adult") },
        { value: "no", label: t("dialogue.fit.age.minor") },
      ];
    }
    return null;
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
    if (turn?.question?.attribute_key === "person.gender") {
      const selectedOption = controlledQuestionOptions(turn.question)?.find(
        (option) => option.value === value,
      );
      submitAnswer(
        { value },
        typeof selectedOption?.label === "string" ? selectedOption.label : value,
      );
      return;
    }
    const selectedOption = turn?.question?.options.find(
      (option) => option.value === value,
    );
    submitAnswer({ value }, selectedOption?.label ?? value);
  }

  const needPickerOptions: ChoiceOption[] = [
    ...availableCategories.map((need) => ({
      value: need.key,
      icon: <NeedSymbol name={need.icon} />,
      label: need.title,
      detail: need.description,
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
          icon: <NeedSymbol name={categoryFor(interpretation.need_key)?.icon ?? "other"} />,
          label: categoryFor(interpretation.need_key)?.title ?? interpretation.need_key,
          detail: t("dialogue.interpretation.confirmHint"),
        },
      ]
    : availableCategories.map((need) => ({
        value: need.key,
        icon: <NeedSymbol name={need.icon} />,
        label: need.title,
        detail: need.description,
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
                    startWithNeed(
                      value as Need,
                      interpretation.workflow_id,
                      interpretation.service_topics ?? [],
                    )
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
          {controlledQuestionHelp(turn.question) && (
            <p className="dialogue-question-help">
              {controlledQuestionHelp(turn.question)}
            </p>
          )}
          <fieldset className="dialogue-answer">
            <legend>{t("dialogue.question.answerLegend")}</legend>
            {controlledQuestionOptions(turn.question) && (
              <ChoiceList
                onSelect={handleAnswerSelect}
                options={[
                  ...(controlledQuestionOptions(turn.question) ?? []),
                  ...skipOptions(turn.question),
                ]}
              />
            )}

            {turn.question.answer_type === "single_choice" &&
              !controlledQuestionOptions(turn.question) && (
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

            {turn.question.answer_type === "yes_no_unknown" &&
              !controlledQuestionOptions(turn.question) && (
              <ChoiceList
                onSelect={handleAnswerSelect}
                options={[
                  { value: "yes", label: t("dialogue.question.yes") },
                  { value: "no", label: t("dialogue.question.no") },
                  ...skipOptions(turn.question),
                ]}
              />
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
            <h2
              id="dialogue-result-heading"
              ref={responseHeadingRef}
              tabIndex={-1}
            >
              {turn.outcome === "no_match"
                ? t("results.noMatch.title")
                : turn.handoff_reason === "immediate_danger"
                  ? t("dialogue.safety.immediateTitle")
                  : turn.handoff_reason === "victim_support_recommended"
                    ? t("dialogue.safety.supportTitle")
                : t("dialogue.result.title")}
            </h2>
          </div>

          {turn.handoff_resources.length > 0 && (
            <section
              aria-label={t("dialogue.safety.resources")}
              className={`safety-resources safety-resources--${turn.handoff_reason}`}
              role={turn.handoff_reason === "immediate_danger" ? "alert" : "region"}
            >
              {turn.handoff_resources.map((resource) => (
                <article className="safety-resource" key={`${resource.kind}-${resource.url}`}>
                  <h3>{resource.name}</h3>
                  <p>{resource.description}</p>
                  <a className="safety-resource-link" href={resource.url}>
                    {resource.phone || t("dialogue.safety.openWebsite")}
                  </a>
                </article>
              ))}
            </section>
          )}

          {turn.candidates.map(({ candidate }) => (
            <article className="result-card" key={candidate.offer.id}>
              {candidate.offer.is_demo && (
                <p className="demo-badge">{t("results.demoBadge")}</p>
              )}
              <div lang={candidate.offer.content_language}>
                <h3>{candidate.offer.name}</h3>
              </div>
              <p className="result-summary" lang={candidate.offer.content_language}>
                {candidate.offer.summary}
              </p>
              {candidate.offer.availability !== "confirmed" && (
                <p className="availability">
                  {candidate.offer.availability === "call_to_confirm"
                    ? t("availability.call_to_confirm")
                    : t("availability.unknown")}
                </p>
              )}
              {(candidate.distance_meters !== null || candidate.offer.address) && (
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
                </div>
              )}
              {candidate.offer.localization_fallback && (
                <p className="uncertainty">{t("results.originalLanguage")}</p>
              )}
              {candidate.offer.contact_note && (
                <p className="contact-note" lang={candidate.offer.content_language}>
                  {candidate.offer.contact_note}
                </p>
              )}
              {(candidate.offer.source.url || candidate.offer.directions_url) && (
                <div className="result-actions">
                  {candidate.offer.source.url && (
                    <a
                      className="offer-link"
                      href={candidate.offer.source.url}
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                      {t("results.source")}
                      <span className="visually-hidden">
                        {" "}
                        ({t("a11y.opensNewTab")})
                      </span>
                    </a>
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
            </article>
          ))}

          {turn.human_handoff_required && turn.handoff_resources.length === 0 && (
            <p className="handoff-message">{t("results.handoff")}</p>
          )}
          {turn.outcome === "no_match" && (
            <div className="no-match-message">
              <p>{t("results.noMatch.text")}</p>
              <Button onClick={restart} variant="secondary">
                {t("results.noMatch.restart")}
              </Button>
            </div>
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
