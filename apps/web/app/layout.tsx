import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import "./globals.css";


export const metadata: Metadata = {
  title: "Vesta – Berner Sozial-Lotse",
  description:
    "Verständliche und verifizierte Orientierung zu sozialen Angeboten in Bern.",
  applicationName: "Vesta",
};

export const viewport: Viewport = {
  colorScheme: "light",
  themeColor: "#f4efe5",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}
