"use client";

import { useI18n } from "@/components/i18n-provider";
import { supportedLocales } from "@/lib/i18n";

export function LocaleSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <label className="locale-switcher">
      <span className="visually-hidden">{t("locale.label")}</span>
      <span aria-hidden="true" className="locale-symbol">
        文
      </span>
      <select
        aria-label={t("locale.label")}
        onChange={(event) => setLocale(event.target.value as typeof locale)}
        value={locale}
      >
        {supportedLocales.map((supportedLocale) => (
          <option key={supportedLocale} value={supportedLocale}>
            {t(`locale.${supportedLocale}`)}
          </option>
        ))}
      </select>
    </label>
  );
}
