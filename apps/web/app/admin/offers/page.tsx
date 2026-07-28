"use client";

import { useCallback, useEffect, useState } from "react";

import { AdminNav } from "@/components/admin-nav";
import { Button } from "@/components/ui";

type AdminOffer = {
  id: string;
  slug: string | null;
  name: string;
  organization_name: string | null;
  summary: string;
  needs: string[];
  languages: string[];
  availability: string;
  published: boolean;
  is_demo: boolean;
  contact_note: string;
  address: string | null;
  source_label: string;
  source_url: string | null;
  verified_at: string;
  updated_at: string | null;
};

type OfferListResponse = {
  offers: AdminOffer[];
  total: number;
  limit: number;
  offset: number;
};

const PAGE_SIZE = 50;

const NEED_LABELS: Record<string, string> = {
  sleep_tonight: "Schlafplatz",
  basic_needs: "Grundbedürfnisse",
  counselling: "Beratung",
};

const AVAILABILITY_LABELS: Record<string, string> = {
  confirmed: "Bestätigt",
  call_to_confirm: "Vorher abklären",
  unknown: "Unbekannt",
};

class RequestError extends Error {
  constructor(readonly status: number) {
    super(`request_failed_${status}`);
  }
}

async function fetchJson<T>(url: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(url, { cache: "no-store", signal });
  if (!response.ok) {
    throw new RequestError(response.status);
  }
  return (await response.json()) as T;
}

function formatTime(value: string | null): string {
  return value ? new Date(value).toLocaleString("de-CH") : "–";
}

function offerRange(offset: number, count: number, total: number): string {
  if (count === 0) {
    return `0 von ${total}`;
  }
  return `${offset + 1}–${offset + count} von ${total}`;
}

export default function AdminOffersPage() {
  const [offers, setOffers] = useState<AdminOffer[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleRequestError = useCallback((requestError: unknown) => {
    if (requestError instanceof RequestError && requestError.status === 401) {
      window.location.replace("/admin/login");
      return;
    }
    if (!(requestError instanceof DOMException && requestError.name === "AbortError")) {
      setError("Angebote konnten nicht geladen werden.");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetchJson<OfferListResponse>(
      `/api/admin/offers?limit=${PAGE_SIZE}&offset=${offset}`,
      controller.signal,
    )
      .then((data) => {
        setOffers(data.offers);
        setTotal(data.total);
      })
      .catch(handleRequestError)
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [handleRequestError, offset]);

  async function logout() {
    const response = await fetch("/api/admin/logout", { method: "POST" });
    if (response.ok) {
      window.location.replace("/admin/login");
      return;
    }
    setError("Abmeldung derzeit nicht möglich.");
  }

  function changePage(nextOffset: number) {
    setLoading(true);
    setError(null);
    setOffset(nextOffset);
  }

  return (
    <main className="admin-shell admin-offers-shell">
      <AdminNav />
      <div className="admin-heading">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Ermittelte Angebote</h1>
        </div>
        <Button onClick={logout} variant="ghost">
          Abmelden
        </Button>
      </div>

      <p className="admin-intro">
        Diese Liste zeigt alle aktuell in Vesta gespeicherten Angebote – auch
        unveröffentlichte Entwürfe und klar gekennzeichnete Demo-Daten.
      </p>

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      {loading && (
        <p aria-live="polite" className="field-hint" role="status">
          Angebote werden geladen …
        </p>
      )}

      {!loading && !error && offers.length === 0 && (
        <p aria-live="polite" className="field-hint" role="status">
          Noch keine Angebote gespeichert.
        </p>
      )}

      {!loading && !error && offers.length > 0 && (
        <>
          <p aria-live="polite" className="admin-result-count" role="status">
            {offerRange(offset, offers.length, total)} Angebote
          </p>
          <div
            aria-label="Ermittelte Angebote, horizontal verschiebbar"
            className="admin-table-scroll"
            role="region"
            tabIndex={0}
          >
            <table className="admin-table admin-offers-table">
              <thead>
                <tr>
                  <th scope="col">Angebot</th>
                  <th scope="col">Organisation</th>
                  <th scope="col">Bereiche</th>
                  <th scope="col">Sprachen</th>
                  <th scope="col">Status</th>
                  <th scope="col">Verfügbarkeit</th>
                  <th scope="col">Standort und Kontakt</th>
                  <th scope="col">Quelle</th>
                  <th scope="col">Aktualisiert</th>
                </tr>
              </thead>
              <tbody>
                {offers.map((offer) => (
                  <tr key={offer.id}>
                    <td className="admin-offer-main">
                      <strong>{offer.name}</strong>
                      <span>{offer.summary}</span>
                      <code>{offer.slug ?? offer.id}</code>
                    </td>
                    <td>{offer.organization_name ?? "–"}</td>
                    <td>
                      {offer.needs
                        .map((need) => NEED_LABELS[need] ?? need)
                        .join(", ")}
                    </td>
                    <td>{offer.languages.map((language) => language.toUpperCase()).join(", ")}</td>
                    <td>
                      <span
                        className={
                          offer.published
                            ? "offer-status offer-status--published"
                            : "offer-status offer-status--draft"
                        }
                      >
                        {offer.published ? "Veröffentlicht" : "Entwurf"}
                      </span>
                      {offer.is_demo && (
                        <span className="offer-status offer-status--demo">Demo</span>
                      )}
                    </td>
                    <td>{AVAILABILITY_LABELS[offer.availability] ?? offer.availability}</td>
                    <td>
                      <span>{offer.address ?? "Kein Standort hinterlegt"}</span>
                      {offer.contact_note && (
                        <span className="admin-offer-secondary">{offer.contact_note}</span>
                      )}
                    </td>
                    <td>
                      {offer.source_url ? (
                        <a href={offer.source_url} rel="noreferrer" target="_blank">
                          {offer.source_label}
                          <span className="visually-hidden"> (öffnet in neuem Tab)</span>
                        </a>
                      ) : (
                        offer.source_label
                      )}
                      <span className="admin-offer-secondary">
                        Geprüft: {formatTime(offer.verified_at)}
                      </span>
                    </td>
                    <td>{formatTime(offer.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <nav aria-label="Seitennavigation der Angebote" className="admin-pagination">
            <Button
              disabled={loading || offset === 0}
              onClick={() => changePage(Math.max(0, offset - PAGE_SIZE))}
              variant="secondary"
            >
              Zurück
            </Button>
            <span>{offerRange(offset, offers.length, total)}</span>
            <Button
              disabled={loading || offset + offers.length >= total}
              onClick={() => changePage(offset + PAGE_SIZE)}
              variant="secondary"
            >
              Weiter
            </Button>
          </nav>
        </>
      )}
    </main>
  );
}
