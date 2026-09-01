"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";

import { AdminNav } from "@/components/admin-nav";
import { Button } from "@/components/ui";

type Category = {
  key: string;
  status: "draft" | "published" | "archived";
  localizations: Record<string, { title: string; description: string }>;
};

type Offer = {
  id: string;
  slug: string;
  name: string;
  organization_name: string;
  summary: string;
  needs: string[];
  languages: string[];
  access_rules: {
    accepts_dogs?: boolean | null;
    identity_document_required?: boolean | null;
    accepted_genders?: string[];
    minimum_age?: number | null;
    maximum_age?: number | null;
  };
  availability: "confirmed" | "call_to_confirm" | "unknown";
  lifecycle: "draft" | "published" | "archived";
  origin: "imported" | "manual";
  management_mode: "source" | "manual";
  revision: number;
  is_demo: boolean;
  contact_note: string;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  source_label: string;
  source_url: string | null;
  verified_by: string;
  verified_at: string;
  expires_at: string;
  updated_at: string;
};

type Change = {
  id: string;
  admin_username: string;
  action: string;
  created_at: string;
};

type OfferDraft = {
  name: string;
  organization_name: string;
  summary: string;
  needs: string[];
  languages: string;
  accepts_dogs: "unknown" | "yes" | "no";
  identity_document_required: "unknown" | "yes" | "no";
  accepted_genders: string;
  minimum_age: string;
  maximum_age: string;
  availability: Offer["availability"];
  contact_note: string;
  address: string;
  latitude: string;
  longitude: string;
  source_label: string;
  source_url: string;
  expires_on: string;
  management_mode: Offer["management_mode"];
  revision?: number;
};

function dateDaysFromNow(days: number) {
  const value = new Date();
  value.setDate(value.getDate() + days);
  return value.toISOString().slice(0, 10);
}

function emptyDraft(): OfferDraft {
  return {
    name: "",
    organization_name: "",
    summary: "",
    needs: [],
    languages: "de",
    accepts_dogs: "unknown",
    identity_document_required: "unknown",
    accepted_genders: "",
    minimum_age: "",
    maximum_age: "",
    availability: "unknown",
    contact_note: "",
    address: "",
    latitude: "",
    longitude: "",
    source_label: "",
    source_url: "",
    expires_on: dateDaysFromNow(30),
    management_mode: "manual",
  };
}

function triState(value: boolean | null | undefined): OfferDraft["accepts_dogs"] {
  return value === true ? "yes" : value === false ? "no" : "unknown";
}

function offerDraft(offer: Offer): OfferDraft {
  return {
    name: offer.name,
    organization_name: offer.organization_name,
    summary: offer.summary,
    needs: offer.needs,
    languages: offer.languages.join(", "),
    accepts_dogs: triState(offer.access_rules.accepts_dogs),
    identity_document_required: triState(offer.access_rules.identity_document_required),
    accepted_genders: (offer.access_rules.accepted_genders ?? []).join(", "),
    minimum_age: offer.access_rules.minimum_age?.toString() ?? "",
    maximum_age: offer.access_rules.maximum_age?.toString() ?? "",
    availability: offer.availability,
    contact_note: offer.contact_note,
    address: offer.address ?? "",
    latitude: offer.latitude?.toString() ?? "",
    longitude: offer.longitude?.toString() ?? "",
    source_label: offer.source_label,
    source_url: offer.source_url ?? "",
    expires_on: offer.expires_at.slice(0, 10),
    management_mode: offer.management_mode,
    revision: offer.revision,
  };
}

function nullableBoolean(value: "unknown" | "yes" | "no") {
  return value === "yes" ? true : value === "no" ? false : null;
}

function nullableNumber(value: string) {
  return value.trim() ? Number(value) : null;
}

function draftPayload(draft: OfferDraft) {
  return {
    name: draft.name.trim(),
    organization_name: draft.organization_name.trim(),
    summary: draft.summary.trim(),
    needs: draft.needs,
    languages: draft.languages.split(",").map((item) => item.trim().toLowerCase()).filter(Boolean),
    access_rules: {
      accepts_dogs: nullableBoolean(draft.accepts_dogs),
      identity_document_required: nullableBoolean(draft.identity_document_required),
      accepted_genders: draft.accepted_genders.split(",").map((item) => item.trim()).filter(Boolean),
      minimum_age: nullableNumber(draft.minimum_age),
      maximum_age: nullableNumber(draft.maximum_age),
    },
    availability: draft.availability,
    contact_note: draft.contact_note.trim(),
    address: draft.address.trim() || null,
    latitude: nullableNumber(draft.latitude),
    longitude: nullableNumber(draft.longitude),
    source_label: draft.source_label.trim(),
    source_url: draft.source_url.trim() || null,
    expires_at: new Date(`${draft.expires_on}T23:59:59`).toISOString(),
    management_mode: draft.management_mode,
    revision: draft.revision,
  };
}

function offerPayload(offer: Offer, needs: string[]) {
  return {
    name: offer.name,
    organization_name: offer.organization_name,
    summary: offer.summary,
    needs,
    languages: offer.languages,
    access_rules: offer.access_rules,
    availability: offer.availability,
    contact_note: offer.contact_note,
    address: offer.address,
    latitude: offer.latitude,
    longitude: offer.longitude,
    source_label: offer.source_label,
    source_url: offer.source_url,
    expires_at: offer.expires_at,
    management_mode: "manual",
    revision: offer.revision,
  };
}

function lifecycleLabel(value: Offer["lifecycle"]) {
  return value === "published" ? "Veröffentlicht" : value === "draft" ? "Entwurf" : "Archiviert";
}

export default function AdminOffersPage() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<OfferDraft>(emptyDraft);
  const [changes, setChanges] = useState<Change[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const activeCategories = categories.filter((item) => item.status === "published");

  const loadData = useCallback(async () => {
    const [offersResponse, categoriesResponse] = await Promise.all([
      fetch("/api/admin/offers?limit=200&offset=0", { cache: "no-store" }),
      fetch("/api/admin/categories", { cache: "no-store" }),
    ]);
    if (offersResponse.status === 401 || categoriesResponse.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    if (!offersResponse.ok || !categoriesResponse.ok) throw new Error("load_failed");
    setOffers(((await offersResponse.json()) as { offers: Offer[] }).offers);
    setCategories(((await categoriesResponse.json()) as { categories: Category[] }).categories);
  }, []);

  useEffect(() => {
    Promise.all([
      fetch("/api/admin/offers?limit=200&offset=0", { cache: "no-store" }),
      fetch("/api/admin/categories", { cache: "no-store" }),
    ])
      .then(async ([offersResponse, categoriesResponse]) => {
        if (offersResponse.status === 401 || categoriesResponse.status === 401) {
          window.location.replace("/admin/login");
          return null;
        }
        if (!offersResponse.ok || !categoriesResponse.ok) {
          throw new Error("load_failed");
        }
        return {
          offers: ((await offersResponse.json()) as { offers: Offer[] }).offers,
          categories: ((await categoriesResponse.json()) as { categories: Category[] }).categories,
        };
      })
      .then((data) => {
        if (!data) return;
        setOffers(data.offers);
        setCategories(data.categories);
      })
      .catch(() => setError("Angebote konnten nicht geladen werden."))
      .finally(() => setLoading(false));
  }, []);

  async function loadChanges(offerId: string) {
    const response = await fetch(`/api/admin/changes?entity_type=offer&entity_id=${encodeURIComponent(offerId)}`, { cache: "no-store" });
    if (response.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    if (response.ok) setChanges(((await response.json()) as { changes: Change[] }).changes);
  }

  function startNew() {
    setSelectedId(null);
    setDraft(emptyDraft());
    setChanges([]);
    setError(null);
    setNotice(null);
  }

  function selectOffer(offer: Offer) {
    setSelectedId(offer.id);
    setDraft(offerDraft(offer));
    setError(null);
    setNotice(null);
    loadChanges(offer.id).catch(() => setChanges([]));
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (draft.needs.length === 0) {
      setError("Ordnen Sie dem Angebot mindestens eine aktive Kategorie zu.");
      return;
    }
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const response = await fetch(selectedId ? `/api/admin/offers/${selectedId}` : "/api/admin/offers", {
        method: selectedId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draftPayload(draft)),
      });
      if (response.status === 401) {
        window.location.replace("/admin/login");
        return;
      }
      const payload = (await response.json()) as Offer & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "save_failed");
      await loadData();
      setSelectedId(payload.id);
      setDraft(offerDraft(payload));
      await loadChanges(payload.id);
      setNotice(selectedId ? "Angebot wurde gespeichert." : "Angebot wurde als Entwurf angelegt.");
    } catch (saveError) {
      const detail = saveError instanceof Error ? saveError.message : "save_failed";
      setError(detail === "offer_was_modified" ? "Das Angebot wurde zwischenzeitlich geändert. Bitte laden Sie es neu." : detail === "unknown_or_inactive_category" ? "Mindestens eine Kategorie ist nicht mehr aktiv." : "Angebot konnte nicht gespeichert werden. Bitte prüfen Sie Pflichtfelder, Quelle und Koordinaten.");
    } finally {
      setSaving(false);
    }
  }

  async function updateMapping(offer: Offer, key: string, checked: boolean) {
    const needs = checked ? [...offer.needs, key] : offer.needs.filter((item) => item !== key);
    if (needs.length === 0) {
      setError("Jedes Angebot benötigt mindestens eine Kategorie.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(`/api/admin/offers/${offer.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(offerPayload(offer, needs)),
      });
      if (response.status === 401) {
        window.location.replace("/admin/login");
        return;
      }
      const payload = (await response.json()) as Offer & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "mapping_failed");
      await loadData();
      if (selectedId === offer.id) {
        setDraft(offerDraft(payload));
        await loadChanges(offer.id);
      }
      setNotice("Kategoriezuordnung wurde gespeichert; manuelle Verwaltung ist aktiv.");
    } catch {
      setError("Kategoriezuordnung konnte nicht gespeichert werden. Bitte laden Sie die Seite neu.");
    } finally {
      setSaving(false);
    }
  }

  async function changeLifecycle(lifecycle: Offer["lifecycle"]) {
    const offer = offers.find((item) => item.id === selectedId);
    if (!offer) return;
    setSaving(true);
    setError(null);
    try {
      const response = await fetch(`/api/admin/offers/${offer.id}/lifecycle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lifecycle, revision: offer.revision }),
      });
      if (response.status === 401) {
        window.location.replace("/admin/login");
        return;
      }
      const payload = (await response.json()) as Offer & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "lifecycle_failed");
      await loadData();
      setDraft(offerDraft(payload));
      await loadChanges(offer.id);
      setNotice(`Status wurde auf „${lifecycleLabel(lifecycle)}“ gesetzt.`);
    } catch (lifecycleError) {
      const detail = lifecycleError instanceof Error ? lifecycleError.message : "";
      setError(detail === "offer_verification_expired" ? "Das Angebot kann erst nach einer erneuten Prüfung mit zukünftigem Ablaufdatum veröffentlicht werden." : "Status konnte nicht geändert werden.");
    } finally {
      setSaving(false);
    }
  }

  async function logout() {
    const response = await fetch("/api/admin/logout", { method: "POST" });
    if (response.ok) window.location.replace("/admin/login");
  }

  return (
    <main className="admin-shell admin-offers-shell" id="main-content">
      <AdminNav />
      <div className="admin-heading"><div><p className="eyebrow">Angebotsregister</p><h1>Angebote & Mapping</h1></div><Button onClick={logout} variant="ghost">Abmelden</Button></div>
      <p className="admin-intro">Die Matrix zeigt, welche aktiven Kategorien zu einem Angebot führen. Eine manuelle Änderung schützt das Angebot vor späterem Überschreiben durch den Import.</p>
      {error && <p className="error-message" role="alert">{error}</p>}
      {notice && <p className="admin-success" role="status">{notice}</p>}

      <section aria-labelledby="mapping-heading" className="admin-panel">
        <div className="admin-panel-heading"><div><h2 id="mapping-heading">Kategorie–Angebot-Mapping</h2><p>{offers.length} Angebote</p></div><Button onClick={startNew} variant="secondary">Neues Angebot</Button></div>
        {loading ? <p aria-live="polite">Angebote werden geladen …</p> : (
          <div className="admin-table-scroll" role="region" aria-label="Kategoriezuordnung der Angebote" tabIndex={0}>
            <table className="admin-table admin-mapping-table">
              <thead><tr><th scope="col">Angebot</th><th scope="col">Status</th><th scope="col">Verwaltung</th>{activeCategories.map((category) => <th key={category.key} scope="col">{category.localizations.de?.title ?? category.key}</th>)}<th scope="col">Aktion</th></tr></thead>
              <tbody>{offers.map((offer) => <tr key={offer.id}>
                <td><strong>{offer.name}</strong><span className="admin-offer-secondary">{offer.organization_name}<br /><code>{offer.slug}</code></span></td>
                <td><span className={`offer-status offer-status--${offer.lifecycle}`}>{lifecycleLabel(offer.lifecycle)}</span></td>
                <td>{offer.origin === "manual" ? "Manuell" : offer.management_mode === "manual" ? "Import · geschützt" : "Import"}</td>
                {activeCategories.map((category) => <td className="mapping-cell" key={category.key}><input aria-label={`${category.localizations.de?.title ?? category.key} für ${offer.name}`} checked={offer.needs.includes(category.key)} disabled={saving || offer.lifecycle === "archived"} onChange={(event) => updateMapping(offer, category.key, event.target.checked)} type="checkbox" /></td>)}
                <td><Button onClick={() => selectOffer(offer)} variant="ghost">Bearbeiten</Button></td>
              </tr>)}</tbody>
            </table>
          </div>
        )}
      </section>

      <section aria-labelledby="offer-editor-heading" className="admin-panel admin-offer-editor">
        <div className="admin-panel-heading"><div><h2 id="offer-editor-heading">{selectedId ? "Angebot bearbeiten" : "Neues Angebot erfassen"}</h2>{selectedId && <p>Änderungen werden historisiert.</p>}</div></div>
        <form onSubmit={save}>
          <fieldset><legend>Grunddaten</legend><div className="admin-form-grid admin-form-grid--three">
            <label className="field" htmlFor="offer-name">Angebotsname<input id="offer-name" maxLength={200} required value={draft.name} onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-organization">Organisation<input id="offer-organization" maxLength={200} required value={draft.organization_name} onChange={(e) => setDraft((d) => ({ ...d, organization_name: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-languages">Sprachen, kommagetrennt<input id="offer-languages" required value={draft.languages} onChange={(e) => setDraft((d) => ({ ...d, languages: e.target.value }))} /></label>
          </div><label className="field" htmlFor="offer-summary">Kurzbeschreibung<textarea id="offer-summary" maxLength={1000} required rows={3} value={draft.summary} onChange={(e) => setDraft((d) => ({ ...d, summary: e.target.value }))} /></label></fieldset>

          <fieldset className="check-group"><legend>Kategorien</legend><div className="admin-checkbox-grid">{activeCategories.map((category) => <label key={category.key}><input checked={draft.needs.includes(category.key)} onChange={(e) => setDraft((d) => ({ ...d, needs: e.target.checked ? [...d.needs, category.key] : d.needs.filter((key) => key !== category.key) }))} type="checkbox" />{category.localizations.de?.title ?? category.key}</label>)}</div></fieldset>

          <fieldset><legend>Zugang und Verfügbarkeit</legend><div className="admin-form-grid admin-form-grid--three">
            <label className="field" htmlFor="offer-availability">Verfügbarkeit<select id="offer-availability" value={draft.availability} onChange={(e) => setDraft((d) => ({ ...d, availability: e.target.value as Offer["availability"] }))}><option value="confirmed">Bestätigt</option><option value="call_to_confirm">Vorher abklären</option><option value="unknown">Unbekannt</option></select></label>
            <label className="field" htmlFor="offer-dogs">Tiere/Hunde<select id="offer-dogs" value={draft.accepts_dogs} onChange={(e) => setDraft((d) => ({ ...d, accepts_dogs: e.target.value as OfferDraft["accepts_dogs"] }))}><option value="unknown">Unbekannt</option><option value="yes">Akzeptiert</option><option value="no">Nicht akzeptiert</option></select></label>
            <label className="field" htmlFor="offer-id">Ausweis erforderlich<select id="offer-id" value={draft.identity_document_required} onChange={(e) => setDraft((d) => ({ ...d, identity_document_required: e.target.value as OfferDraft["identity_document_required"] }))}><option value="unknown">Unbekannt</option><option value="yes">Ja</option><option value="no">Nein</option></select></label>
            <label className="field" htmlFor="offer-genders">Zielgruppen, kommagetrennt<input id="offer-genders" value={draft.accepted_genders} onChange={(e) => setDraft((d) => ({ ...d, accepted_genders: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-min-age">Mindestalter<input id="offer-min-age" max="120" min="0" type="number" value={draft.minimum_age} onChange={(e) => setDraft((d) => ({ ...d, minimum_age: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-max-age">Höchstalter<input id="offer-max-age" max="120" min="0" type="number" value={draft.maximum_age} onChange={(e) => setDraft((d) => ({ ...d, maximum_age: e.target.value }))} /></label>
          </div></fieldset>

          <fieldset><legend>Kontakt und Standort</legend><label className="field" htmlFor="offer-contact">Kontakt- und Zugangshinweis<textarea id="offer-contact" maxLength={2000} required rows={3} value={draft.contact_note} onChange={(e) => setDraft((d) => ({ ...d, contact_note: e.target.value }))} /></label><div className="admin-form-grid admin-form-grid--three">
            <label className="field" htmlFor="offer-address">Adresse<input id="offer-address" value={draft.address} onChange={(e) => setDraft((d) => ({ ...d, address: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-latitude">Breitengrad<input id="offer-latitude" max="90" min="-90" step="any" type="number" value={draft.latitude} onChange={(e) => setDraft((d) => ({ ...d, latitude: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-longitude">Längengrad<input id="offer-longitude" max="180" min="-180" step="any" type="number" value={draft.longitude} onChange={(e) => setDraft((d) => ({ ...d, longitude: e.target.value }))} /></label>
          </div></fieldset>

          <fieldset><legend>Quelle und Prüfung</legend><div className="admin-form-grid admin-form-grid--three">
            <label className="field" htmlFor="offer-source-label">Quellenbezeichnung<input id="offer-source-label" required value={draft.source_label} onChange={(e) => setDraft((d) => ({ ...d, source_label: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-source-url">Quellenlink<input id="offer-source-url" type="url" value={draft.source_url} onChange={(e) => setDraft((d) => ({ ...d, source_url: e.target.value }))} /></label>
            <label className="field" htmlFor="offer-expires">Geprüft bis<input id="offer-expires" required type="date" value={draft.expires_on} onChange={(e) => setDraft((d) => ({ ...d, expires_on: e.target.value }))} /></label>
            {selectedId && <label className="field" htmlFor="offer-management">Verwaltung<select id="offer-management" value={draft.management_mode} onChange={(e) => setDraft((d) => ({ ...d, management_mode: e.target.value as Offer["management_mode"] }))}><option value="manual">Manuell geschützt</option><option value="source">Beim nächsten Import aus Quelle übernehmen</option></select></label>}
          </div></fieldset>

          <div className="admin-form-actions"><Button disabled={saving} type="submit">{saving ? "Wird gespeichert …" : "Entwurf speichern"}</Button>{selectedId && <><Button disabled={saving} onClick={() => changeLifecycle("published")} variant="secondary">Veröffentlichen</Button><Button disabled={saving} onClick={() => changeLifecycle("draft")} variant="ghost">Veröffentlichung zurückziehen</Button><Button disabled={saving} onClick={() => changeLifecycle("archived")} variant="ghost">Archivieren</Button></>}<Button onClick={startNew} variant="ghost">Eingaben verwerfen</Button></div>
        </form>

        {selectedId && <section aria-labelledby="offer-history-heading" className="admin-history"><h3 id="offer-history-heading">Änderungshistorie</h3>{changes.length ? <ol>{changes.map((change) => <li key={change.id}><time dateTime={change.created_at}>{new Date(change.created_at).toLocaleString("de-CH")}</time> · {change.admin_username} · {change.action}</li>)}</ol> : <p>Noch keine protokollierten Änderungen.</p>}</section>}
      </section>
    </main>
  );
}
