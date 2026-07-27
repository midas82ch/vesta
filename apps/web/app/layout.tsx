import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { I18nProvider } from "@/components/i18n-provider";
import { ServiceWorkerRegistration } from "@/components/pwa-controls";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://www.vesta-app.ch"),
  title: "Vesta – Weniger Systemreibung. Mehr Zugang zu Hilfe.",
  description:
    "Der verifizierte, mehrsprachige Sozial-Lotse für Bern: passende Hilfe finden, Fachpersonen entlasten und Systemlücken sichtbar machen.",
  applicationName: "Vesta",
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "Vesta – Berner Sozial-Lotse",
    description:
      "Weniger Systemreibung, mehr Zugang zu Hilfe: verständlich, mehrsprachig und mit sichtbaren Quellen.",
    type: "website",
    url: "/",
    siteName: "Vesta",
    locale: "de_CH",
  },
  twitter: {
    card: "summary",
    title: "Vesta – Berner Sozial-Lotse",
    description:
      "Weniger Systemreibung, mehr Zugang zu Hilfe: verständlich, mehrsprachig und mit sichtbaren Quellen.",
  },
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Vesta",
  },
  formatDetection: {
    telephone: true,
  },
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4efe5" },
    { media: "(prefers-color-scheme: dark)", color: "#164f47" },
  ],
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html dir="ltr" lang="de-CH" suppressHydrationWarning>
      <body>
        <I18nProvider>
          <ServiceWorkerRegistration />
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}
