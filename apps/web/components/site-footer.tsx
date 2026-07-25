"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";

export function SiteFooter() {
  const { locale, t } = useI18n();

  return (
    <footer>
      <p>{t("footer.emergency")}</p>
      <div className="footer-meta">
        <p>{t("footer.prototype")}</p>
        <Link href={`/impressum?lang=${locale}`}>{t("footer.imprint")}</Link>
      </div>
    </footer>
  );
}
