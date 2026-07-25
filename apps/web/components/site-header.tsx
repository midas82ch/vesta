"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n-provider";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { PwaInstallButton } from "@/components/pwa-controls";
import { VestaMark } from "@/components/vesta-mark";

type SiteHeaderProps = {
  currentPage: "home" | "imprint" | "privacy";
};

export function SiteHeader({ currentPage }: Readonly<SiteHeaderProps>) {
  const { locale, t } = useI18n();
  const homeHref = `/?lang=${locale}`;
  const imprintHref = `/impressum?lang=${locale}`;
  const privacyHref = `/datenschutz?lang=${locale}`;

  return (
    <header className="site-header">
      <Link className="brand" href={homeHref} aria-label={t("brand.homeLabel")}>
        <span className="brand-mark" aria-hidden="true">
          <VestaMark />
        </span>
        <span>Vesta</span>
      </Link>

      <nav className="primary-nav" aria-label={t("nav.primaryLabel")}>
        <Link
          aria-current={currentPage === "home" ? "page" : undefined}
          href={homeHref}
        >
          {t("nav.home")}
        </Link>
        <Link
          aria-current={currentPage === "imprint" ? "page" : undefined}
          href={imprintHref}
        >
          {t("nav.imprint")}
        </Link>
        <Link
          aria-current={currentPage === "privacy" ? "page" : undefined}
          href={privacyHref}
        >
          {t("nav.privacy")}
        </Link>
      </nav>

      <div className="header-actions">
        <p className="pilot-label">{t("pilot.label")}</p>
        <PwaInstallButton />
        <LocaleSwitcher />
      </div>
    </header>
  );
}
