"use client";

import { useI18n } from "@/components/i18n-provider";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { NavigatorForm } from "@/components/navigator-form";
import { PwaInstallButton } from "@/components/pwa-controls";
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

export default function Home() {
  const { t } = useI18n();

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t("a11y.skipToContent")}
      </a>
      <header className="site-header">
        <a className="brand" href="#start" aria-label={t("brand.homeLabel")}>
          <span className="brand-mark" aria-hidden="true">
            V
          </span>
          <span>Vesta</span>
        </a>
        <div className="header-actions">
          <p className="pilot-label">{t("pilot.label")}</p>
          <PwaInstallButton />
          <LocaleSwitcher />
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <section className="hero" id="start">
          <div className="hero-copy">
            <p className="eyebrow">{t("hero.eyebrow")}</p>
            <h1>{t("hero.title")}</h1>
            <p className="lead">{t("hero.lead")}</p>
            <div className="trust-note">
              <span className="trust-dot" aria-hidden="true" />
              <p>{t("hero.trust")}</p>
            </div>
          </div>

          <NavigatorForm />
        </section>

        <section className="principles" aria-labelledby="principles-title">
          <div className="section-heading">
            <p className="eyebrow">{t("principles.eyebrow")}</p>
            <h2 id="principles-title">{t("principles.title")}</h2>
          </div>
          <div className="principle-grid">
            {principles.map((principle) => (
              <article className="principle-card" key={principle.number}>
                <p className="principle-number">{principle.number}</p>
                <h3>{t(principle.title)}</h3>
                <p>{t(principle.text)}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer>
        <p>{t("footer.emergency")}</p>
        <p>{t("footer.prototype")}</p>
      </footer>
    </>
  );
}
