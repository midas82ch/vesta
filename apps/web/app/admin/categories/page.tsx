"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";

import { AdminNav } from "@/components/admin-nav";
import { NeedSymbol } from "@/components/need-symbol";
import { Button } from "@/components/ui";
import type { NeedIcon } from "@/lib/needs";

const LOCALES = [
  ["de", "Deutsch"],
  ["fr", "Französisch"],
  ["en", "Englisch"],
  ["es", "Spanisch"],
  ["pt", "Portugiesisch"],
  ["ary", "Darija"],
] as const;

const ICONS: { value: NeedIcon; label: string }[] = [
  { value: "home", label: "Haus / Schlafplatz" },
  { value: "food", label: "Nahrung" },
  { value: "book", label: "Beratung / Buch" },
  { value: "health", label: "Gesundheit" },
  { value: "clothing", label: "Kleidung" },
  { value: "shower", label: "Hygiene / Dusche" },
  { value: "support", label: "Unterstützung" },
  { value: "other", label: "Andere Kategorie" },
];

type Localization = { title: string; description: string };
type Category = {
  key: string;
  icon: NeedIcon;
  status: "draft" | "published" | "archived";
  sort_order: number;
  revision: number;
  localizations: Record<string, Localization>;
  offer_count: number;
};

type CategoryDraft = {
  icon: NeedIcon;
  status: Category["status"];
  sort_order: number;
  revision?: number;
  localizations: Record<string, Localization>;
};

function emptyDraft(sortOrder: number): CategoryDraft {
  return {
    icon: "other",
    status: "draft",
    sort_order: sortOrder,
    localizations: Object.fromEntries(
      LOCALES.map(([locale]) => [locale, { title: "", description: "" }]),
    ),
  };
}

function categoryDraft(category: Category): CategoryDraft {
  return {
    icon: category.icon,
    status: category.status,
    sort_order: category.sort_order,
    revision: category.revision,
    localizations: structuredClone(category.localizations),
  };
}

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [draft, setDraft] = useState<CategoryDraft>(() => emptyDraft(10));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadCategories = useCallback(async () => {
    const response = await fetch("/api/admin/categories", { cache: "no-store" });
    if (response.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    if (!response.ok) throw new Error("categories_failed");
    const data = (await response.json()) as { categories: Category[] };
    setCategories(data.categories);
  }, []);

  useEffect(() => {
    fetch("/api/admin/categories", { cache: "no-store" })
      .then((response) => {
        if (response.status === 401) {
          window.location.replace("/admin/login");
          return null;
        }
        if (!response.ok) throw new Error("categories_failed");
        return response.json() as Promise<{ categories: Category[] }>;
      })
      .then((data) => {
        if (data) setCategories(data.categories);
      })
      .catch(() => setError("Kategorien konnten nicht geladen werden."))
      .finally(() => setLoading(false));
  }, []);

  function selectCategory(category: Category) {
    setSelectedKey(category.key);
    setDraft(categoryDraft(category));
    setError(null);
    setNotice(null);
  }

  function startNewCategory() {
    const nextOrder = Math.max(0, ...categories.map((item) => item.sort_order)) + 10;
    setSelectedKey(null);
    setDraft(emptyDraft(nextOrder));
    setError(null);
    setNotice(null);
  }

  function updateLocalization(
    locale: string,
    field: keyof Localization,
    value: string,
  ) {
    setDraft((current) => ({
      ...current,
      localizations: {
        ...current.localizations,
        [locale]: { ...current.localizations[locale], [field]: value },
      },
    }));
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const url = selectedKey
        ? `/api/admin/categories/${encodeURIComponent(selectedKey)}`
        : "/api/admin/categories";
      const response = await fetch(url, {
        method: selectedKey ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      if (response.status === 401) {
        window.location.replace("/admin/login");
        return;
      }
      const payload = (await response.json()) as Category & { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail ?? "save_failed");
      }
      await loadCategories();
      setSelectedKey(payload.key);
      setDraft(categoryDraft(payload));
      setNotice(
        selectedKey
          ? "Kategorie wurde gespeichert."
          : `Kategorie „${payload.localizations.de.title}“ wurde als ${payload.status === "draft" ? "Entwurf" : "aktiv"} angelegt.`,
      );
    } catch (saveError) {
      const detail = saveError instanceof Error ? saveError.message : "save_failed";
      setError(
        detail === "category_still_has_offers"
          ? "Die Kategorie kann erst archiviert werden, wenn ihr keine Angebote mehr zugeordnet sind."
          : detail === "category_was_modified"
            ? "Die Kategorie wurde zwischenzeitlich geändert. Bitte laden Sie sie neu."
            : "Kategorie konnte nicht gespeichert werden. Bitte prüfen Sie alle Übersetzungen.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function logout() {
    const response = await fetch("/api/admin/logout", { method: "POST" });
    if (response.ok) window.location.replace("/admin/login");
  }

  return (
    <main className="admin-shell admin-catalog-shell" id="main-content">
      <AdminNav />
      <div className="admin-heading">
        <div>
          <p className="eyebrow">Angebotsregister</p>
          <h1>Kategorien</h1>
        </div>
        <Button onClick={logout} variant="ghost">Abmelden</Button>
      </div>
      <p className="admin-intro">
        Kategorien steuern die öffentliche Bedarfsauswahl und das Matching. Ein
        technischer Schlüssel wird beim Anlegen automatisch aus dem deutschen Namen
        erzeugt und bleibt danach stabil.
      </p>

      {error && <p className="error-message" role="alert">{error}</p>}
      {notice && <p className="admin-success" role="status">{notice}</p>}

      <div className="admin-catalog-layout">
        <section aria-labelledby="category-list-heading" className="admin-panel">
          <div className="admin-panel-heading">
            <h2 id="category-list-heading">Vorhandene Kategorien</h2>
            <Button onClick={startNewCategory} variant="secondary">
              Neue Kategorie
            </Button>
          </div>
          {loading ? (
            <p aria-live="polite">Kategorien werden geladen …</p>
          ) : (
            <table className="admin-compact-table">
              <thead>
                <tr><th scope="col">Name</th><th scope="col">Status</th><th scope="col">Angebote</th><th scope="col"><span className="visually-hidden">Aktion</span></th></tr>
              </thead>
              <tbody>
                {categories.map((category) => (
                  <tr key={category.key}>
                    <td>
                      <span className="admin-category-name">
                        <NeedSymbol name={category.icon} />
                        <span><strong>{category.localizations.de?.title ?? category.key}</strong><code>{category.key}</code></span>
                      </span>
                    </td>
                    <td>{category.status === "published" ? "Aktiv" : category.status === "draft" ? "Entwurf" : "Archiviert"}</td>
                    <td>{category.offer_count}</td>
                    <td><Button onClick={() => selectCategory(category)} variant="ghost">Bearbeiten</Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section aria-labelledby="category-editor-heading" className="admin-panel admin-editor-panel">
          <h2 id="category-editor-heading">{selectedKey ? "Kategorie bearbeiten" : "Neue Kategorie"}</h2>
          {selectedKey && <p className="field-hint">Technischer Schlüssel: <code>{selectedKey}</code></p>}
          <form onSubmit={save}>
            <div className="admin-form-grid admin-form-grid--three">
              <label className="field" htmlFor="category-icon">Symbol
                <select id="category-icon" value={draft.icon} onChange={(event) => setDraft((current) => ({ ...current, icon: event.target.value as NeedIcon }))}>
                  {ICONS.map((icon) => <option key={icon.value} value={icon.value}>{icon.label}</option>)}
                </select>
              </label>
              <label className="field" htmlFor="category-order">Reihenfolge
                <input id="category-order" min="0" type="number" value={draft.sort_order} onChange={(event) => setDraft((current) => ({ ...current, sort_order: Number(event.target.value) }))} />
              </label>
              <label className="field" htmlFor="category-status">Status
                <select id="category-status" value={draft.status} onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value as Category["status"] }))}>
                  <option value="draft">Entwurf</option>
                  <option value="published">Aktiv</option>
                  <option value="archived">Archiviert</option>
                </select>
              </label>
            </div>
            <div className="admin-localization-grid">
              {LOCALES.map(([locale, label]) => (
                <fieldset className="admin-translation" dir={locale === "ary" ? "rtl" : "ltr"} key={locale}>
                  <legend>{label}</legend>
                  <label className="field" htmlFor={`category-${locale}-title`}>Name
                    <input id={`category-${locale}-title`} maxLength={120} required value={draft.localizations[locale]?.title ?? ""} onChange={(event) => updateLocalization(locale, "title", event.target.value)} />
                  </label>
                  <label className="field" htmlFor={`category-${locale}-description`}>Kurzbeschreibung
                    <textarea id={`category-${locale}-description`} maxLength={300} required rows={3} value={draft.localizations[locale]?.description ?? ""} onChange={(event) => updateLocalization(locale, "description", event.target.value)} />
                  </label>
                </fieldset>
              ))}
            </div>
            <div className="admin-form-actions">
              <Button disabled={saving} type="submit">{saving ? "Wird gespeichert …" : "Kategorie speichern"}</Button>
              <Button onClick={startNewCategory} variant="ghost">Eingaben verwerfen</Button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
