"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { Button } from "@/components/ui";
import { VestaMark } from "@/components/vesta-mark";

export default function OfflinePage() {
  const { t } = useI18n();

  return (
    <main className="offline-page" id="main-content">
      <div className="offline-toolbar">
        <Link className="brand" href="/" aria-label={t("brand.homeLabel")}>
          <span className="brand-mark" aria-hidden="true">
            <VestaMark />
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
          <Button icon="↻" onClick={() => window.location.reload()}>
            {t("offline.retry")}
          </Button>
          <Button href="/" variant="ghost">
            {t("offline.back")}
          </Button>
        </div>
      </section>
    </main>
  );
}
