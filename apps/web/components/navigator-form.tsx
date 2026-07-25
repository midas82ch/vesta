"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";

import { useI18n } from "@/components/i18n-provider";
import type { MessageKey } from "@/lib/i18n";


export type Need = "sleep_tonight" | "basic_needs" | "counselling";

type Candidate = {
  offer: {
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
  reasons: string[];
  uncertainties: string[];
};

type MatchResponse = {
  candidates: Candidate[];
  human_handoff_required: boolean;
  handoff_reason: string | null;
  disclaimer: string;
};

export type NeedOption = {
  value: Need;
  title: MessageKey;
  detail: MessageKey;
  icon: string;
};

export const needs: NeedOption[] = [
  {
    value: "sleep_tonight",
    title: "need.sleep.title",
    detail: "need.sleep.detail",
    icon: "⌂",
  },
  {
    value: "basic_needs",
    title: "need.basic.title",
    detail: "need.basic.detail",
    icon: "+",
  },
  {
    value: "counselling",
    title: "need.counselling.title",
    detail: "need.counselling.detail",
    icon: "→",
  },
];

const availabilityKeys: Record<
  Candidate["offer"]["availability"],
  MessageKey
> = {
  confirmed: "availability.confirmed",
  call_to_confirm: "availability.call_to_confirm",
  unknown: "availability.unknown",
};

export function NavigatorForm() {
  const { formatDate, formatResultCount, locale, t } = useI18n();
  const [selectedNeed, setSelectedNeed] = useState<Need>("sleep_tonight");
  const [targetGroup, setTargetGroup] = useState("");
  const [dog, setDog] = useState(false);
  const [hasIdentityDocument, setHasIdentityDocument] = useState(true);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    "idle",
  );
  const [result, setResult] = useState<MatchResponse | null>(null);
  const errorRef = useRef<HTMLParagraphElement>(null);
  const resultHeadingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (status === "error") {
      errorRef.current?.focus();
    }

    if (status === "success") {
      resultHeadingRef.current?.focus();
    }
  }, [status]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("loading");
    setResult(null);

    try {
      const response = await fetch("/api/matches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          need: selectedNeed,
          language: locale,
          gender: targetGroup || null,
          dog,
          has_identity_document: hasIdentityDocument,
          risk_flags: [],
        }),
      });

      if (!response.ok) {
        throw new Error("request_failed");
      }

      setResult((await response.json()) as MatchResponse);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="navigator-card">
      <form
        aria-busy={status === "loading"}
        aria-describedby="navigator-help"
        onSubmit={submit}
      >
        <p className="visually-hidden" id="navigator-help">
          {t("form.help")}
        </p>

        <fieldset>
          <legend>{t("form.need.legend")}</legend>
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
                  name="need"
                  onChange={() => setSelectedNeed(need.value)}
                  type="radio"
                  value={need.value}
                />
              </label>
            ))}
          </div>
        </fieldset>

        <div className="form-row">
          <label className="select-label" htmlFor="target-group">
            {t("form.targetGroup.label")}
            <select
              aria-describedby="target-group-hint"
              id="target-group"
              value={targetGroup}
              onChange={(event) => setTargetGroup(event.target.value)}
            >
              <option value="">{t("form.targetGroup.none")}</option>
              <option value="finta">{t("form.targetGroup.finta")}</option>
              <option value="other">{t("form.targetGroup.other")}</option>
            </select>
            <span className="field-hint" id="target-group-hint">
              {t("form.targetGroup.hint")}
            </span>
          </label>

          <fieldset className="check-group">
            <legend>{t("form.additional.legend")}</legend>
            <label>
              <input
                checked={dog}
                onChange={(event) => setDog(event.target.checked)}
                type="checkbox"
              />
              <span>{t("form.dog")}</span>
            </label>
            <label>
              <input
                checked={!hasIdentityDocument}
                onChange={(event) =>
                  setHasIdentityDocument(!event.target.checked)
                }
                type="checkbox"
              />
              <span>{t("form.noIdentity")}</span>
            </label>
          </fieldset>
        </div>

        <button
          className="primary-button"
          disabled={status === "loading"}
          type="submit"
        >
          <span>
            {status === "loading" ? t("form.loading") : t("form.submit")}
          </span>
          <span aria-hidden="true">→</span>
        </button>

        {status === "loading" && (
          <p className="visually-hidden" role="status">
            {t("status.loading")}
          </p>
        )}
      </form>

      <div
        aria-atomic="false"
        aria-live="polite"
        className="result-region"
      >
        {status === "error" && (
          <p
            className="error-message"
            ref={errorRef}
            role="alert"
            tabIndex={-1}
          >
            {t("error.search")}
          </p>
        )}

        {status === "success" && result && (
          <div className="results">
            <div
              className="result-heading"
              ref={resultHeadingRef}
              tabIndex={-1}
            >
              <p className="eyebrow">{t("results.eyebrow")}</p>
              <h2>{formatResultCount(result.candidates.length)}</h2>
            </div>

            {result.candidates.map((candidate) => (
              <article className="result-card" key={candidate.offer.id}>
                {candidate.offer.is_demo && (
                  <p className="demo-badge">{t("results.demoBadge")}</p>
                )}
                <div lang="de">
                  <h3>{candidate.offer.name}</h3>
                  <p>{candidate.offer.summary}</p>
                </div>
                {locale !== "de" && (
                  <p className="original-language-note">
                    {t("results.originalLanguage")}
                  </p>
                )}
                <p className="availability">
                  {t(availabilityKeys[candidate.offer.availability])}
                </p>
                {candidate.uncertainties.length > 0 && (
                  <p className="uncertainty">{t("results.uncertainty")}</p>
                )}
                <p className="contact-note" lang="de">
                  {candidate.offer.contact_note}
                </p>
                <p className="source">
                  {t("results.checked", {
                    date: formatDate(candidate.offer.source.verified_at),
                  })}{" "}
                  · {t("results.source")}:{" "}
                  {candidate.offer.source.url ? (
                    <a
                      href={candidate.offer.source.url}
                      rel="noopener noreferrer"
                      target="_blank"
                    >
                      <span lang="de">{candidate.offer.source.label}</span>
                      <span className="visually-hidden">
                        {" "}
                        ({t("a11y.opensNewTab")})
                      </span>
                    </a>
                  ) : (
                    <span lang="de">{candidate.offer.source.label}</span>
                  )}
                </p>
              </article>
            ))}

            {result.human_handoff_required && (
              <p className="handoff-message">{t("results.handoff")}</p>
            )}
            <p className="disclaimer">{t("results.disclaimer")}</p>
          </div>
        )}
      </div>
    </div>
  );
}
