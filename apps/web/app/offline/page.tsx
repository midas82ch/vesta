"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";
import { LocaleSwitcher } from "@/components/locale-switcher";


export default function OfflinePage() {
  const { t } = useI18n();

  return (
    <main className="offline-page" id="main-content">
      <div className="offline-toolbar">
        <Link className="brand" href="/" aria-label={t("brand.homeLabel")}>
          <span className="brand-mark" aria-hidden="true">
            V
          </span>
          <span>Vesta</span>
        </Link>
        <LocaleSwitcher />
      </div>

      <section className="offline-card" aria-labelledby="offline-title">
        <p className="eyebrow">{t("offline.eyebrow")}</p>
        <h1 id="offline-title">{t("offline.title")}</h1>
        <p className="lead">{t("offline.body")}</p>
        <div className="offline-actions">
          <button
            className="primary-button"
            onClick={() => window.location.reload()}
            type="button"
          >
            <span>{t("offline.retry")}</span>
            <span aria-hidden="true">↻</span>
          </button>
          <Link className="secondary-link" href="/">
            {t("offline.back")}
          </Link>
        </div>
      </section>
    </main>
  );
}
