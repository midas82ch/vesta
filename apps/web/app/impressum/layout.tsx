import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Über Vesta & Impressum",
  description:
    "Zweck, Arbeitsweise, Pilotstatus und rechtliche Angaben zu Vesta.",
  alternates: {
    canonical: "/impressum",
  },
};

export default function ImprintLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return children;
}
