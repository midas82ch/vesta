"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ADMIN_LINKS = [
  { href: "/admin/ai-audit", label: "AI-Audit" },
  { href: "/admin/offers", label: "Angebote" },
  { href: "/admin/offer-imports", label: "URL-Import" },
  { href: "/admin/categories", label: "Kategorien & Mapping" },
  { href: "/admin/ingestion-runs", label: "Angebots-Prüfung" },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav aria-label="Admin-Navigation" className="admin-nav">
      {ADMIN_LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            aria-current={active ? "page" : undefined}
            className={active ? "admin-nav-link admin-nav-link-active" : "admin-nav-link"}
            href={link.href}
            key={link.href}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
