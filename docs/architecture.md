# Architektur

## Leitprinzip

Die AI-Schicht versteht und vereinfacht Sprache. Deterministische,
versionierte Regeln prüfen Sicherheit und Zugang. Eine Fachperson übernimmt
unsichere, komplexe oder kritische Situationen.

```text
Mobile PWA / Fachansicht
          |
          v
     HTTP API
          |
   +------+-------------------+
   |                          |
Sicherheitsregeln        Dialog-Adapter
   |                     (später LLM)
   v                          |
Matching-Service <------------+
   |
   +--> verifiziertes Angebotsregister
   +--> versionierte Zugangsregeln
   +--> anonymisierte Wirkungssignale
```

## Komponenten

### Web

Die Next.js-PWA ist der primäre Zugang. Sie ist mobil, tastaturbedienbar und
auf wenig Text ausgelegt. Die erste Version benötigt kein Konto und speichert
keine fallbezogenen Daten im Browser.

### API

FastAPI stellt explizit versionierte Endpunkte bereit. Transportmodelle werden
von der Fachlogik getrennt. So kann dieselbe Matching-Logik später in der
Fachpersonenansicht oder in einem Kiosk verwendet werden.

### Sicherheitsprüfung

Die Sicherheitsprüfung läuft vor jeder Angebotssuche. Kritische Hinweise
führen in einen freigegebenen, nicht-generativen Übergabeprozess. Inhalte und
Kontakte dieses Prozesses müssen lokal fachlich geprüft werden.

### Matching

Matching ist nachvollziehbar und ohne Sprachmodell testbar:

1. abgelaufene oder nicht veröffentlichte Angebote ausschliessen
2. Bedarf und Zielgruppe prüfen
3. harte Zugangskriterien prüfen
4. Öffnungs- und Statusinformationen berücksichtigen
5. verbleibende Angebote nach fachlicher Eignung sortieren
6. bei gleicher Eignung optional die Luftliniendistanz berücksichtigen

Jedes Ergebnis enthält passende Gründe sowie Unsicherheiten. Der freiwillig
freigegebene Standort verändert nie Sicherheits- oder Zugangskriterien und
blendet weiter entfernte Angebote nicht aus (ADR 0007).

### Angebotsregister

PostgreSQL ist die spätere führende Datenquelle. PostGIS unterstützt
Entfernungssuchen; pgvector kann freigegebene Dokumente semantisch auffindbar
machen. Das initiale Dateirepository erlaubt Entwicklung und Tests ohne
Datenbank. Es enthält nur klar markierte Beispieldaten. Angebotsstandorte sind
öffentliche, quellengeprüfte Katalogdaten.

Die über `data/sources/bern_offers.json` automatisiert eingelesenen Angebote
sind seit dem 27.07.2026 einzeln verifiziert (nicht mehr pauschal als
Testdaten markiert, `is_demo = false`). Ein täglicher systemd-Timer
(`infra/systemd/vesta-offer-ingest.timer`) prüft die hinterlegten
Bestätigungssätze auf den Quell-Webseiten erneut und hält die Datenbank
aktuell; die Lauf-Historie ist im Adminbereich unter „Angebots-Prüfung"
einsehbar.

### AI-Adapter

Ein Sprachmodell wird erst hinter einer schmalen Schnittstelle ergänzt. Seine
Ausgabe muss in ein strukturiertes Anfrageformat validiert werden. Antworten
dürfen nur Inhalte aus freigegebenen Quellen erklären und müssen deren
Aktualität sichtbar machen.

## Datenschutz

- Datensparsamkeit und anonyme Nutzung sind Standard.
- Angebots-, Nutzungs- und allfällige spätere Begleitdaten werden getrennt.
- Freitext wird im MVP nicht dauerhaft gespeichert.
- Logs enthalten technische IDs, keine vollständigen Eingaben.
- Analyseereignisse bilden Bedarf und Ergebnis ab, nicht Personenprofile.
- Ein optional freigegebener Browserstandort wird auf drei Dezimalstellen
  gerundet, nur für die aktuelle Distanzberechnung verwendet und weder
  gespeichert noch an das AI-Modell übermittelt. Auch konkrete Distanzen
  werden nicht im Workflow-Audit abgelegt (ADR 0007).
- Ausnahme: tatsächlich versuchte AI-Gateway-Interaktionen
  (Freitext-Interpretation, Fragen-Formulierung, Ergebnis-Erklärung) werden
  im Volltext protokolliert, um den KI-Entscheidungsprozess prüfbar zu
  machen (ADR 0005). Zusätzlich verbindet eine Workflow-Spur Eingaben,
  deterministische Frageauswahl und Matching-Logik, AI-Aufrufe und die
  öffentliche Antwort über dieselbe technische Workflow-ID (ADR 0006).
  Diese Daten bleiben bis zu einer späteren manuellen Löschung gespeichert
  und sind ausschliesslich über den per Login geschützten Adminbereich
  einsehbar.

## Menschliche Übergabe

Die Übergabe wird ausgelöst, wenn:

- eine Sicherheitsregel greift
- keine verlässliche Information vorhanden ist
- widersprüchliche Zugangskriterien bestehen
- die Person ausdrücklich menschliche Hilfe wünscht
- ein Angebot eine telefonische Abklärung verlangt

## Geplante Ausbaustufen

1. Verifiziertes Register und drei MVP-Situationen
2. Pflegeportal mit Verantwortlichkeiten und Prüfworkflow
3. Kontrollierte Mehrsprachigkeit sowie Sprach-Ein-/Ausgabe
4. Freiwilliger pseudonymer Begleitmodus nach eigener Datenschutzprüfung

Microservices, eigene Modelltrainings und zentrale Personendossiers sind für
diese Ausbaustufen nicht erforderlich.
