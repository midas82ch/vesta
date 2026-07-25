"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import type { MessageKey } from "@/lib/i18n";

const principles: Array<{
  number: string;
  title: MessageKey;
  text: MessageKey;
}> = [
  {
    number: "01",
    title: "principle.verified.title",
    text: "principle.verified.text",
  },
  {
    number: "02",
    title: "principle.rules.title",
    text: "principle.rules.text",
  },
  {
    number: "03",
    title: "principle.handoff.title",
    text: "principle.handoff.text",
  },
];

export default function ImprintPage() {
  const { locale, t } = useI18n();

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t("a11y.skipToContent")}
      </a>
      <SiteHeader currentPage="imprint" />

      <main className="imprint-main" id="main-content" tabIndex={-1}>
        <article className="imprint-card">
          <header className="imprint-intro">
            <p className="eyebrow">{t("about.eyebrow")}</p>
            <h1>{t("about.title")}</h1>
            <p className="lead">{t("about.lead")}</p>
          </header>

          <section className="imprint-section" aria-labelledby="problem-title">
            <p className="eyebrow">{t("about.problem.eyebrow")}</p>
            <h2 id="problem-title">{t("about.problem.title")}</h2>
            <p>{t("about.problem.text")}</p>
            <div className="audience-grid">
              <article>
                <h3>{t("about.people.title")}</h3>
                <p>{t("about.people.text")}</p>
              </article>
              <article>
                <h3>{t("about.professionals.title")}</h3>
                <p>{t("about.professionals.text")}</p>
              </article>
              <article>
                <h3>{t("about.system.title")}</h3>
                <p>{t("about.system.text")}</p>
              </article>
            </div>
          </section>

          <section className="imprint-section" aria-labelledby="how-title">
            <p className="eyebrow">{t("principles.eyebrow")}</p>
            <h2 id="how-title">{t("principles.title")}</h2>
            <ol className="imprint-principles">
              {principles.map((principle) => (
                <li key={principle.number}>
                  <span className="principle-number" aria-hidden="true">
                    {principle.number}
                  </span>
                  <div>
                    <h3>{t(principle.title)}</h3>
                    <p>{t(principle.text)}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section
            className="imprint-section responsibility-section"
            aria-labelledby="responsibility-title"
          >
            <p className="eyebrow">{t("about.responsibility.eyebrow")}</p>
            <h2 id="responsibility-title">
              {t("about.responsibility.title")}
            </h2>
            <p>{t("about.responsibility.text")}</p>
          </section>

          <section className="imprint-section" aria-labelledby="pilot-title">
            <p className="eyebrow">{t("about.pilot.eyebrow")}</p>
            <h2 id="pilot-title">{t("about.pilot.title")}</h2>
            <p>{t("about.pilot.text")}</p>
            <p className="section-note">{t("about.pilot.note")}</p>
          </section>

          <section className="imprint-section legal-section" aria-labelledby="legal-title">
            <p className="eyebrow">{t("imprint.eyebrow")}</p>
            <h2 id="legal-title">{t("imprint.title")}</h2>
            <dl className="imprint-details">
              <div>
                <dt>{t("imprint.project.label")}</dt>
                <dd>{t("imprint.project.value")}</dd>
              </div>
              <div>
                <dt>{t("imprint.status.label")}</dt>
                <dd>{t("imprint.status.value")}</dd>
              </div>
              <div>
                <dt>{t("imprint.responsibility.label")}</dt>
                <dd>{t("imprint.responsibility.value")}</dd>
              </div>
              <div>
                <dt>{t("imprint.contact.label")}</dt>
                <dd>
                  <a
                    href="https://github.com/midas82ch/vesta"
                    rel="noreferrer"
                    target="_blank"
                  >
                    {t("imprint.contact.value")}
                    <span className="visually-hidden">
                      {" "}
                      ({t("a11y.opensNewTab")})
                    </span>
                  </a>
                </dd>
              </div>
            </dl>
            <p className="imprint-notice">{t("imprint.note")}</p>
            <p className="source-code-link">
              <a
                href="https://github.com/midas82ch/vesta"
                rel="noreferrer"
                target="_blank"
              >
                {t("about.pilot.link")}
                <span className="visually-hidden">
                  {" "}
                  ({t("a11y.opensNewTab")})
                </span>
              </a>
            </p>
          </section>

          <Link className="back-link" href={`/?lang=${locale}`}>
            <span aria-hidden="true">←</span>
            {t("about.back")}
          </Link>
        </article>
      </main>

      <SiteFooter />
    </>
  );
}
