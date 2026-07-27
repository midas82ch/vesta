"use client";

import Link from "next/link";
import type { MouseEvent } from "react";

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

  function reloadHome(event: MouseEvent<HTMLAnchorElement>) {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return;
    }

    event.preventDefault();
    window.location.assign(homeHref);
  }

  return (
    <header className="site-header">
      <Link
        className="brand"
        href={homeHref}
        aria-label={t("brand.homeLabel")}
        onClick={reloadHome}
      >
        <span className="brand-mark" aria-hidden="true">
          <VestaMark />
        </span>
        <span>Vesta</span>
      </Link>

      <nav className="primary-nav" aria-label={t("nav.primaryLabel")}>
        <Link
          aria-current={currentPage === "home" ? "page" : undefined}
          href={homeHref}
          onClick={reloadHome}
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
