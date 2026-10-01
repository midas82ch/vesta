"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";

import { AdminNav } from "@/components/admin-nav";
import { NeedSymbol } from "@/components/need-symbol";
import { Button } from "@/components/ui";
import type { ServiceIcon } from "@/lib/needs";

const LOCALES = [
  ["de", "Deutsch"], ["fr", "Französisch"], ["en", "Englisch"],
  ["es", "Spanisch"], ["pt", "Portugiesisch"], ["ary", "Darija"],
] as const;
const ICONS: ServiceIcon[] = [
  "meal", "groceries", "shower", "laundry", "clothing", "toilet", "locker",
  "chat", "housing", "wallet", "health", "mental-health", "legal", "support",
  "alcohol", "medication", "substances", "multiple", "question", "daytime", "other",
];
type Localization = { label: string; description: string };
type Service = {
  key: string;
  service_group: "basic_needs" | "counselling" | "addiction";
  icon: ServiceIcon;
  status: "draft" | "published" | "archived";
  sort_order: number;
  revision: number;
  localizations: Record<string, Localization>;
  offer_count: number;
};
type Draft = Omit<Service, "key" | "offer_count">;

function emptyDraft(order: number): Draft {
  return {
    service_group: "basic_needs", icon: "other", status: "draft",
    sort_order: order, revision: 0,
    localizations: Object.fromEntries(
      LOCALES.map(([locale]) => [locale, { label: "", description: "" }]),
    ),
  };
}

export default function AdminServicesPage() {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft>(() => emptyDraft(10));
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const response = await fetch("/api/admin/services", { cache: "no-store" });
    if (response.status === 401) return window.location.replace("/admin/login");
    if (!response.ok) throw new Error("load_failed");
    setServices(((await response.json()) as { services: Service[] }).services);
  }, []);
  useEffect(() => {
    fetch("/api/admin/services", { cache: "no-store" })
      .then((response) => {
        if (response.status === 401) {
          window.location.replace("/admin/login");
          return null;
        }
        if (!response.ok) throw new Error("load_failed");
        return response.json() as Promise<{ services: Service[] }>;
      })
      .then((payload) => {
        if (payload) setServices(payload.services);
      })
      .catch(() => setError("Leistungen konnten nicht geladen werden."));
  }, []);

  function startNew() {
    setSelectedKey(null);
    setDraft(emptyDraft(Math.max(0, ...services.map((item) => item.sort_order)) + 10));
    setError(null); setNotice(null);
  }
  function select(item: Service) {
    setSelectedKey(item.key);
    setDraft({
      service_group: item.service_group, icon: item.icon, status: item.status,
      sort_order: item.sort_order, revision: item.revision,
      localizations: structuredClone(item.localizations),
    });
    setError(null); setNotice(null);
  }
  function localize(locale: string, field: keyof Localization, value: string) {
    setDraft((current) => ({ ...current, localizations: {
      ...current.localizations,
      [locale]: { ...current.localizations[locale], [field]: value },
    } }));
  }
  async function save(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null); setNotice(null);
    try {
      const response = await fetch(
        selectedKey ? `/api/admin/services/${encodeURIComponent(selectedKey)}` : "/api/admin/services",
        { method: selectedKey ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...draft, revision: selectedKey ? draft.revision : undefined }) },
      );
      if (response.status === 401) return window.location.replace("/admin/login");
      const payload = (await response.json()) as Service & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "save_failed");
      await load(); select(payload); setNotice("Leistung wurde gespeichert.");
    } catch (reason) {
      const detail = reason instanceof Error ? reason.message : "save_failed";
      setError(detail === "service_still_has_offers" ? "Eine verwendete Leistung kann nicht archiviert werden." : detail === "service_group_limit_reached" ? "Pro Auswahlschritt sind höchstens sieben aktive Kacheln erlaubt. Legen Sie für weitere Merkmale einen Folgeschritt an." : "Leistung konnte nicht gespeichert werden. Bitte alle Sprachfassungen prüfen.");
    } finally { setSaving(false); }
  }

  return <main className="admin-shell admin-catalog-shell" id="main-content">
    <AdminNav />
    <div className="admin-heading"><div><p className="eyebrow">Angebotsregister</p><h1>Leistungsmerkmale</h1></div></div>
    <p className="admin-intro">Diese Merkmale steuern die Icon-Auswahl und sind harte Filter. Nur quellenbelegte Leistungen dürfen Angeboten zugeordnet werden.</p>
    {error && <p className="error-message" role="alert">{error}</p>}
    {notice && <p className="admin-success" role="status">{notice}</p>}
    <div className="admin-catalog-layout">
      <section className="admin-panel" aria-labelledby="service-list"><div className="admin-panel-heading"><h2 id="service-list">Leistungen</h2><Button onClick={startNew} variant="secondary">Neue Leistung</Button></div>
        <table className="admin-compact-table"><thead><tr><th>Name</th><th>Gruppe</th><th>Angebote</th><th><span className="visually-hidden">Aktion</span></th></tr></thead><tbody>{services.map((item) => <tr key={item.key}><td><span className="admin-category-name"><NeedSymbol name={item.icon} /><span><strong>{item.localizations.de?.label ?? item.key}</strong><code>{item.key}</code></span></span></td><td>{item.service_group}</td><td>{item.offer_count}</td><td><Button onClick={() => select(item)} variant="ghost">Bearbeiten</Button></td></tr>)}</tbody></table>
      </section>
      <section className="admin-panel admin-editor-panel" aria-labelledby="service-editor"><h2 id="service-editor">{selectedKey ? "Leistung bearbeiten" : "Neue Leistung"}</h2>
        <form onSubmit={save}><div className="admin-form-grid admin-form-grid--three">
          <label className="field">Gruppe<select value={draft.service_group} onChange={(event) => setDraft((value) => ({ ...value, service_group: event.target.value as Draft["service_group"] }))}><option value="basic_needs">Grundversorgung</option><option value="counselling">Beratung</option><option value="addiction">Sucht-Präzisierung</option></select></label>
          <label className="field">Symbol<select value={draft.icon} onChange={(event) => setDraft((value) => ({ ...value, icon: event.target.value as ServiceIcon }))}>{ICONS.map((icon) => <option key={icon}>{icon}</option>)}</select></label>
          <label className="field">Status<select disabled={!selectedKey} value={draft.status} onChange={(event) => setDraft((value) => ({ ...value, status: event.target.value as Draft["status"] }))}><option value="draft">Entwurf</option><option value="published">Aktiv</option><option value="archived">Archiviert</option></select></label>
          <label className="field">Reihenfolge<input min="0" type="number" value={draft.sort_order} onChange={(event) => setDraft((value) => ({ ...value, sort_order: Number(event.target.value) }))} /></label>
        </div><div className="admin-localization-grid">{LOCALES.map(([locale, label]) => <fieldset className="admin-translation" dir={locale === "ary" ? "rtl" : "ltr"} key={locale}><legend>{label}</legend><label className="field">Bezeichnung<input maxLength={120} required value={draft.localizations[locale]?.label ?? ""} onChange={(event) => localize(locale, "label", event.target.value)} /></label><label className="field">Abgrenzung<textarea maxLength={300} rows={3} value={draft.localizations[locale]?.description ?? ""} onChange={(event) => localize(locale, "description", event.target.value)} /></label></fieldset>)}</div><div className="admin-form-actions"><Button disabled={saving} type="submit">{saving ? "Wird gespeichert …" : "Leistung speichern"}</Button><Button onClick={startNew} variant="ghost">Eingaben verwerfen</Button></div></form>
      </section>
    </div>
  </main>;
}
