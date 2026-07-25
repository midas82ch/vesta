import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { I18nProvider } from "@/components/i18n-provider";
import { ServiceWorkerRegistration } from "@/components/pwa-controls";

import "./globals.css";


export const metadata: Metadata = {
  title: "Vesta – Berner Sozial-Lotse",
  description:
    "Verständliche und verifizierte Orientierung zu sozialen Angeboten in Bern.",
  applicationName: "Vesta",
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
