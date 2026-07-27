"use client";

import { useI18n } from "@/components/i18n-provider";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui";
import type { MessageKey } from "@/lib/i18n";

const sections: Array<{
  id: string;
  eyebrow: MessageKey;
  title: MessageKey;
  text: MessageKey;
}> = [
  {
    id: "scope",
    eyebrow: "privacy.scope.eyebrow",
    title: "privacy.scope.title",
    text: "privacy.scope.text",
  },
  {
    id: "location",
    eyebrow: "privacy.location.eyebrow",
    title: "privacy.location.title",
    text: "privacy.location.text",
  },
  {
    id: "storage",
    eyebrow: "privacy.storage.eyebrow",
    title: "privacy.storage.title",
    text: "privacy.storage.text",
  },
  {
    id: "device",
    eyebrow: "privacy.device.eyebrow",
    title: "privacy.device.title",
    text: "privacy.device.text",
  },
  {
    id: "offline",
    eyebrow: "privacy.offline.eyebrow",
    title: "privacy.offline.title",
    text: "privacy.offline.text",
  },
  {
    id: "logs",
    eyebrow: "privacy.logs.eyebrow",
    title: "privacy.logs.title",
    text: "privacy.logs.text",
  },
  {
    id: "offers",
    eyebrow: "privacy.offers.eyebrow",
    title: "privacy.offers.title",
    text: "privacy.offers.text",
  },
  {
    id: "ai",
    eyebrow: "privacy.ai.eyebrow",
    title: "privacy.ai.title",
    text: "privacy.ai.text",
  },
  {
    id: "hosting",
    eyebrow: "privacy.hosting.eyebrow",
    title: "privacy.hosting.title",
    text: "privacy.hosting.text",
  },
  {
    id: "rights",
    eyebrow: "privacy.rights.eyebrow",
    title: "privacy.rights.title",
    text: "privacy.rights.text",
  },
  {
    id: "responsible",
    eyebrow: "privacy.responsible.eyebrow",
    title: "privacy.responsible.title",
    text: "privacy.responsible.text",
  },
];

export default function PrivacyPage() {
  const { locale, t } = useI18n();

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t("a11y.skipToContent")}
      </a>
      <SiteHeader currentPage="privacy" />

      <main className="imprint-main" id="main-content" tabIndex={-1}>
        <article className="imprint-card">
          <header className="imprint-intro">
            <p className="eyebrow">{t("privacy.eyebrow")}</p>
            <h1>{t("privacy.title")}</h1>
            <p className="lead">{t("privacy.lead")}</p>
          </header>

          {sections.map((section) => (
            <section
              className="imprint-section"
              aria-labelledby={`${section.id}-title`}
              key={section.id}
            >
              <p className="eyebrow">{t(section.eyebrow)}</p>
              <h2 id={`${section.id}-title`}>{t(section.title)}</h2>
              <p>{t(section.text)}</p>
              {section.id === "scope" ? (
                <p className="section-note">{t("privacy.scope.noAccount")}</p>
              ) : null}
            </section>
          ))}

          <section
            className="imprint-section legal-section"
            aria-labelledby="privacy-contact-title"
          >
            <p className="eyebrow">{t("imprint.eyebrow")}</p>
            <h2 id="privacy-contact-title">{t("privacy.contact.label")}</h2>
            <p>
              <a href="mailto:info@vesta-app.ch">
                info@vesta-app.ch
              </a>
            </p>
            <p>
              <a
                href="https://github.com/midas82ch/vesta"
                rel="noreferrer"
                target="_blank"
              >
                {t("privacy.contact.value")}
                <span className="visually-hidden">
                  {" "}
                  ({t("a11y.opensNewTab")})
                </span>
              </a>
            </p>
            <p className="imprint-notice">{t("privacy.note")}</p>
          </section>

          <Button href={`/?lang=${locale}`} icon="←" iconPosition="start" variant="ghost">
            {t("about.back")}
          </Button>
        </article>
      </main>

      <SiteFooter />
    </>
  );
}
