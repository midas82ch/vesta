"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useSyncExternalStore,
} from "react";

import {
  defaultLocale,
  getDirection,
  interpolate,
  localeTags,
  messages,
  type Locale,
  type MessageKey,
  normalizeLocale,
  resultCountKey,
} from "@/lib/i18n";

type I18nContextValue = {
  locale: Locale;
  direction: "ltr" | "rtl";
  setLocale: (locale: Locale) => void;
  t: (
    key: MessageKey,
    values?: Record<string, string | number>,
  ) => string;
  formatDate: (value: Date | string) => string;
  formatNumber: (value: number) => string;
  formatResultCount: (count: number) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);
const localeChangeEvent = "vesta-locale-change";

function detectLocale(): Locale {
  const queryLocale = normalizeLocale(
    new URLSearchParams(window.location.search).get("lang"),
  );
  let storedLocale: Locale | null = null;

  try {
    storedLocale = normalizeLocale(window.localStorage.getItem("vesta-locale"));
  } catch {
    // Some privacy modes deliberately block storage. The URL and browser locale
    // remain fully functional fallbacks.
  }

  const browserLanguages =
    navigator.languages.length > 0 ? navigator.languages : [navigator.language];
  const browserLocale = browserLanguages
    .map((language) => normalizeLocale(language))
    .find((locale): locale is Locale => locale !== null);

  return queryLocale ?? storedLocale ?? browserLocale ?? defaultLocale;
}

function subscribeToLocaleChange(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(localeChangeEvent, callback);

  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(localeChangeEvent, callback);
  };
}

export function I18nProvider({ children }: Readonly<{ children: ReactNode }>) {
  const locale = useSyncExternalStore(
    subscribeToLocaleChange,
    detectLocale,
    () => defaultLocale,
  );

  const setLocale = useCallback((nextLocale: Locale) => {
    try {
      window.localStorage.setItem("vesta-locale", nextLocale);
    } catch {
      // The query parameter below still persists the selection for this URL.
    }

    const url = new URL(window.location.href);
    url.searchParams.set("lang", nextLocale);
    window.history.replaceState({}, "", url);
    window.dispatchEvent(new Event(localeChangeEvent));
  }, []);

  useEffect(() => {
    document.documentElement.lang = localeTags[locale];
    document.documentElement.dir = getDirection(locale);
    try {
      window.localStorage.setItem("vesta-locale", locale);
    } catch {
      // Storage is optional; language and direction still update in the DOM.
    }
  }, [locale]);

  const value = useMemo<I18nContextValue>(() => {
    const formatNumber = (number: number) =>
      new Intl.NumberFormat(localeTags[locale]).format(number);

    const t = (
      key: MessageKey,
      values: Record<string, string | number> = {},
    ) => interpolate(messages[locale][key], values);

    return {
      locale,
      direction: getDirection(locale),
      setLocale,
      t,
      formatDate: (dateValue) =>
        new Intl.DateTimeFormat(localeTags[locale], {
          day: "numeric",
          month: "long",
          year: "numeric",
        }).format(
          typeof dateValue === "string" ? new Date(dateValue) : dateValue,
        ),
      formatNumber,
      formatResultCount: (count) =>
        t(resultCountKey(locale, count), {
          count: formatNumber(count),
        }),
    };
  }, [locale, setLocale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error("useI18n must be used inside I18nProvider");
  }

  return context;
}
