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

## Repository

```text
apps/
  api/                  FastAPI und deterministisches Matching
  web/                  Mobile Next.js-PWA
data/
  seed/                 Ausschliesslich geprüfte oder klar markierte Testdaten
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
printf '%s' "$DATABASE_URI" > secrets/database-url
unset DATABASE_URI
chmod 600 secrets/database-url
sudo docker compose -f compose.prod.yaml up --build -d
sudo docker compose -f compose.prod.yaml ps
```

Die URI muss TLS aktivieren (`sslmode=require` oder stärker). Der Ordner
`secrets/` wird von Git und vom Docker-Build-Kontext ausgeschlossen. Vor dem
API-Start führt Compose alle noch offenen Alembic-Migrationen aus.

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
