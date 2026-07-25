"use client";

import { useI18n } from "@/components/i18n-provider";
import { NavigatorForm } from "@/components/navigator-form";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  const { t } = useI18n();

  return (
    <>
      <a className="skip-link" href="#main-content">
        {t("a11y.skipToContent")}
      </a>
      <SiteHeader currentPage="home" />

      <main id="main-content" tabIndex={-1}>
        <section className="hero" id="start">
          <div className="hero-copy">
            <p className="eyebrow">{t("hero.eyebrow")}</p>
            <h1>{t("hero.title")}</h1>
            <p className="lead">{t("hero.lead")}</p>
          </div>

          <NavigatorForm />
        </section>
      </main>

      <SiteFooter />
    </>
  );
}
