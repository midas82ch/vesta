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

Gewalt-, Bedrohungs- und Akutformulierungen werden in allen sechs unterstützten
Sprachen deterministisch erkannt, bevor ein AI-Aufruf stattfindet. Der
anschließende Sicherheitsdialog ist ebenfalls nicht-generativ: unmittelbare
Gefahr führt zu 117 und 144; sonst werden 142 und ausschließlich geprüfte
Opferhilfe-Angebote angezeigt (ADR 0009).

### Matching

Matching ist nachvollziehbar und ohne Sprachmodell testbar (ADR 0011):

1. nicht veröffentlichte, institutionell nicht freigegebene oder endgültig
   abgelaufene Angebote ausschliessen
2. Bedarf und Zielgruppe prüfen
3. bestätigte Leistungsmerkmale als harte Kriterien prüfen
4. bestätigte Zugangsangaben einschliesslich exakter Altersgrenzen prüfen
5. Öffnungs- und Statusinformationen berücksichtigen
6. verbleibende Angebote nach fachlicher Eignung sortieren
7. Dubletten derselben Institution zusammenführen
8. bei gleicher Eignung optional die Luftliniendistanz berücksichtigen
9. höchstens drei bestplatzierte Angebote öffentlich ausgeben

Grundversorgung und Beratung werden über beschriftete Icon-Kacheln
präzisiert. Die bestätigte Auswahl wird als `requested_services` an den
Matching-Kern gegeben. Freitext darf Kacheln vorauswählen, ersetzt aber nie
die Bestätigung der Person.

Ein konkretes Alter wird nur erfragt, wenn es eine verbleibende Altersregel
tatsächlich entscheidet. Der Wert bleibt flüchtig in der Dialogsession, wird
nicht an AI übergeben und weder im Workflow-Audit noch im Markdown-Export
gespeichert. `person.is_adult` bleibt für eine Übergangsrelease kompatibel
(ADR 0011).

Matching-Gründe, Unsicherheiten und tiefer rangierte Angebote werden im
Workflow-Audit festgehalten, aber nicht in der öffentlichen Oberfläche
angezeigt. Dort stehen die geprüfte Angebotsbeschreibung und der nächste
Schritt im Vordergrund. Der freiwillig freigegebene Standort verändert nie
Sicherheits- oder Zugangskriterien (ADR 0007, ADR 0010).

### Angebotsregister

PostgreSQL ist die spätere führende Datenquelle. PostGIS unterstützt
Entfernungssuchen; pgvector kann freigegebene Dokumente semantisch auffindbar
machen. Das initiale Dateirepository erlaubt Entwicklung und Tests ohne
Datenbank. Es enthält nur klar markierte Beispieldaten. Angebotsstandorte sind
öffentliche, quellengeprüfte Katalogdaten.

Die über `data/sources/bern_offers.json` automatisiert eingelesenen Angebote
sind seit dem 27.07.2026 einzeln verifiziert (nicht mehr pauschal als
Testdaten markiert, `is_demo = false`). Ihre Slugs tragen seit der Migration
`20260728_0008` auch keinen historischen `test-`-Präfix mehr. Ein täglicher
systemd-Timer
(`infra/systemd/vesta-offer-ingest.timer`) prüft die hinterlegten
Bestätigungssätze auf den Quell-Webseiten erneut und hält die Datenbank
aktuell; die Lauf-Historie ist im Adminbereich unter „Angebots-Prüfung"
einsehbar.

Leistungsmerkmale werden separat mit Quelle, Status und Prüfzeitpunkt
gespeichert. Nur `confirmed`-Merkmale nehmen am öffentlichen Matching teil.
Neue Quellenwerte werden als Importrevision zur Gegenüberstellung gespeichert
und überschreiben die öffentliche Fassung nicht. Die institutionelle
Zustimmung wird mit Umfang und Nachweis dokumentiert. Neue Angebote benötigen
`approved`; bestehende Einträge dürfen höchstens 90 Tage `legacy_pending`
bleiben. Nach Ablauf einer Angebotsprüfung gilt eine 30-tägige Warnfrist mit
telefonischem Abklärungshinweis, danach wird der Eintrag ausgeblendet.

Kategorien und ihre sechs Übersetzungen werden ebenfalls in PostgreSQL
geführt und von der öffentlichen Bedarfsauswahl dynamisch geladen. Der
geschützte, desktop-orientierte Adminbereich zeigt das Kategorie-Angebots-
Mapping als Matrix. Neue manuelle Angebote werden als Entwurf angelegt und
separat veröffentlicht. Eine manuelle Übernahme (`management_mode = manual`)
schützt Felder, Mapping und Verifikation vor nachfolgenden Quellenimporten.
Der automatische Import kann über eine revisionierte, protokollierte
Schalter-Einstellung deaktiviert werden (ADR 0008).

Zusätzlich können Admins einzelne HTTPS-Quellen als persistente URL-Aufträge
erfassen. Ein eigener Worker prüft Netzwerkziel und Redirects gegen SSRF,
beachtet `robots.txt`, extrahiert einen Angebotsentwurf und erzeugt sechs
maschinelle Übersetzungsentwürfe. Erst eine aktuelle Quellenprüfung, eine
geprüfte deutsche Sprachfassung und ein separater Freigabeschritt machen ein
Angebot öffentlich. Maschinelle Übersetzungen werden nie automatisch
veröffentlicht (ADR 0009).

### AI-Adapter

Ein Sprachmodell wird erst hinter einer schmalen Schnittstelle ergänzt. Seine
Ausgabe muss in ein strukturiertes Anfrageformat validiert werden. Im
öffentlichen Dialog unterstützt es das Sprachverständnis und erlaubte
Frageformulierungen. Die Ergebnisansicht verwendet ausschließlich geprüfte
Angebotstexte und keine generierte Begründung (ADR 0010).

## Datenschutz

- Datensparsamkeit und anonyme Nutzung sind Standard.
- Angebots-, Nutzungs- und allfällige spätere Begleitdaten werden getrennt.
- Freitext wird im MVP nicht dauerhaft gespeichert.
- Logs enthalten technische IDs, keine vollständigen Eingaben.
- Analyseereignisse bilden Bedarf und Ergebnis ab, nicht Personenprofile.
- Ein für Altersregeln benötigtes konkretes Alter bleibt ausschliesslich im
  Arbeitsspeicher der laufenden Dialogsession. Es wird nicht an AI übergeben,
  nicht protokolliert und nicht exportiert; nur das Resultat der Altersprüfung
  darf im Audit erscheinen (ADR 0011).
- Ein optional freigegebener Browserstandort wird auf drei Dezimalstellen
  gerundet, nur für die aktuelle Distanzberechnung verwendet und weder
  gespeichert noch an das AI-Modell übermittelt. Auch konkrete Distanzen
  werden nicht im Workflow-Audit abgelegt (ADR 0007).
- Ausnahme: tatsächlich versuchte AI-Gateway-Interaktionen
  (Freitext-Interpretation, Fragen-Formulierung und Import-Aufbereitung; in
  älteren Spuren auch Ergebnis-Erklärungen) werden
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
- widersprüchliche Zugangskriterien bestehen
- die Person ausdrücklich menschliche Hilfe wünscht
- ein Angebot eine telefonische Abklärung verlangt

Wenn die deterministische Suche kein passendes, aktuelles Angebot findet, ist
dies dagegen ein reguläres `no_match`-Ergebnis. Es wird transparent angezeigt
und nicht als Sicherheits-Weiterleitung ausgegeben (ADR 0008).

## Geplante Ausbaustufen

1. Verifiziertes Register und vier MVP-Situationen
2. Pflegeportal mit Verantwortlichkeiten und Prüfworkflow
3. Kontrollierte Mehrsprachigkeit sowie Sprach-Ein-/Ausgabe
4. Freiwilliger pseudonymer Begleitmodus nach eigener Datenschutzprüfung

Microservices, eigene Modelltrainings und zentrale Personendossiers sind für
diese Ausbaustufen nicht erforderlich.
