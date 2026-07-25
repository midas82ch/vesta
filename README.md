# Vesta – Berner Sozial-Lotse

Vesta ist die technische Grundlage für einen verifizierten, mehrsprachigen
Sozial-Lotsen für Bern. Das System soll Menschen in schwierigen Lebenslagen
schneller zu passenden Angeboten führen und Fachpersonen bei der Recherche
entlasten.

Der wichtigste Grundsatz: AI darf Sprache verstehen und erklären, aber nicht
entscheiden, wer Hilfe erhält. Zugangskriterien, Aktualität und
Sicherheitseskalationen bleiben nachvollziehbare Regeln.

## MVP

Der erste Pilot konzentriert sich auf drei Situationen:

1. Einen Schlafplatz für heute Nacht finden.
2. Essen, Dusche oder medizinische Ersthilfe finden.
3. Beratung zu Sucht, Wohnen oder finanziellen Problemen finden.

Es werden keine Personendossiers, automatischen Zuteilungen oder medizinischen
Diagnosen erstellt.

## Web-Oberfläche

Die Oberfläche ist mobile-first aufgebaut und unterstützt Deutsch,
Französisch, Englisch und Arabisch. Die Sprachwahl bleibt in der URL und – wo
vom Browser erlaubt – lokal gespeichert. Arabisch wird mit
Rechts-nach-links-Layout dargestellt; Datumsangaben und Ergebniszahlen werden
sprachabhängig formatiert.

Vesta ist als installierbare PWA ausgelegt. Der Service Worker speichert nur
die Anwendungshülle und statische Ressourcen. API-Antworten mit Angeboten
werden bewusst nicht offline gespeichert, damit keine möglicherweise
veralteten Sozialangebote angezeigt werden. Ohne Verbindung erscheint
stattdessen eine mehrsprachige Offline-Seite.

Die Web-Oberfläche zielt auf WCAG 2.2 AA: semantische Formulare, sichtbare
Tastaturfokusse, Skip-Link, Statusmeldungen für Assistenztechnologien,
mindestens 44 Pixel grosse Bedienflächen sowie Unterstützung für reduzierte
Bewegung und erzwungene Kontrastfarben.

## Repository

```text
apps/
  api/                  FastAPI und deterministisches Matching
  web/                  Mobile Next.js-PWA
data/
  seed/                 Ausschliesslich geprüfte oder klar markierte Testdaten
  sources/              Kuratierte öffentliche Quellen und Evidenzbegriffe
docs/
  adr/                  Architekturentscheide
  architecture.md       System- und Sicherheitsarchitektur
  hosting.md            Hosting-Empfehlung und Zieltopologie
  product-scope.md      MVP-Umfang und Erfolgsmessung
infra/
  postgres/             PostgreSQL mit PostGIS und pgvector
packages/
  contracts/            Gemeinsame JSON-Schemas
```

## Lokal starten

Voraussetzungen:

- Docker mit Compose
- Node.js 22 und Corepack
- Python 3.12

Konfiguration kopieren:

```bash
cp .env.example .env
```

Entwicklungsdienste starten:

```bash
docker compose up --build
```

- Web: <http://localhost:3000>
- API-Dokumentation: <http://localhost:8000/docs>
- API-Status: <http://localhost:8000/health>
- API-Bereitschaft inklusive Datenbank: <http://localhost:8000/ready>

Alternativ können Web und API einzeln gestartet werden:

```bash
corepack enable
pnpm install
pnpm dev:web
```

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"
python -m uvicorn vesta_api.main:app --reload
```

Unter macOS/Linux lautet der letzte Installationspfad
`.venv/bin/pip`.

## Checks

```bash
pnpm lint
pnpm typecheck
pnpm build
cd apps/api
python -m unittest discover -s tests
```

## Auf einer einzelnen VM mit Managed PostgreSQL starten

Für den technischen Prototyp steht eine separate Compose-Datei bereit. Sie
veröffentlicht nur Caddy auf Port 80 und 443. Web und API bleiben in internen
Docker-Netzen; PostgreSQL läuft als verwalteter Exoscale-Dienst.

```bash
cp .env.example .env
# VESTA_SITE_ADDRESS in .env setzen
install -d -m 700 secrets
read -rsp "Exoscale PostgreSQL URI: " DATABASE_URI
printf '%s' "$DATABASE_URI" > secrets/database-admin-url
unset DATABASE_URI
chmod 600 secrets/database-admin-url
sudo docker compose -f compose.prod.yaml build api migrate
sudo docker compose -f compose.prod.yaml run --rm migrate
sudo docker run --rm \
  -e DATABASE_ADMIN_URL_FILE=/run/secrets/database-admin-url \
  -e DATABASE_SECRET_OUTPUT=/run/vesta-secret-output \
  -v "$PWD/secrets/database-admin-url:/run/secrets/database-admin-url:ro" \
  -v "$PWD/secrets:/run/vesta-secret-output" \
  vesta-api:latest \
  python -m vesta_api.cli.provision_database_roles
sudo docker compose -f compose.prod.yaml up -d --wait
sudo docker compose -f compose.prod.yaml ps
```

Die URI muss TLS aktivieren (`sslmode=require` oder stärker). Der Ordner
`secrets/` wird von Git und vom Docker-Build-Kontext ausgeschlossen. Vor dem
API-Start führt Compose alle noch offenen Alembic-Migrationen aus.
`avnadmin` wird nur für Migrationen verwendet. Die API verbindet sich als
`vesta_app` mit Leserechten; der Quellenimport verwendet `vesta_ingest` mit
Schreibrechten ausschliesslich auf den Angebotstabellen.

## Öffentliche Testangebote aktualisieren

`data/sources/bern_offers.json` enthält kuratierte, offizielle Berner
Quellseiten. Der Importer respektiert `robots.txt`, lädt höchstens 2 MB pro
Seite und akzeptiert einen Datensatz nur, wenn alle hinterlegten
Evidenzbegriffe weiterhin vorkommen. Er übernimmt keine freien Kapazitäten und
markiert jeden Datensatz sichtbar als Test.

Quellen ohne Datenbankzugriff prüfen:

```bash
cd apps/api
python -m vesta_api.cli.check_offer_sources
```

Import manuell ausführen:

```bash
sudo docker compose -f compose.prod.yaml \
  --profile jobs run --rm --no-deps ingest
```

Für die tägliche Ausführung stehen eine One-shot-Unit und ein Timer bereit:

```bash
sudo install -m 644 infra/systemd/vesta-offer-ingest.service \
  /etc/systemd/system/vesta-offer-ingest.service
sudo install -m 644 infra/systemd/vesta-offer-ingest.timer \
  /etc/systemd/system/vesta-offer-ingest.timer
sudo systemctl daemon-reload
sudo systemctl enable --now vesta-offer-ingest.timer
systemctl list-timers vesta-offer-ingest.timer
```

Für einen ersten Test über eine IP-Adresse wird beispielsweise
`VESTA_SITE_ADDRESS=http://203.0.113.10` gesetzt. Sobald ein DNS-Name auf die
VM zeigt, wird stattdessen der Domainname ohne `http://` eingetragen; Caddy
bezieht und erneuert dann automatisch das TLS-Zertifikat.

Die Beispieldaten unter `data/seed` sind ausdrücklich keine publizierbaren
Angebotsdaten. Reale Daten müssen vor der Verwendung einer verantwortlichen
Organisation, Quelle, Prüfung und einem Ablaufdatum zugeordnet werden.

Mehr Kontext steht in [docs/product-scope.md](docs/product-scope.md) und
[docs/architecture.md](docs/architecture.md). Die Hosting-Empfehlung ist in
[docs/hosting.md](docs/hosting.md) festgehalten.
