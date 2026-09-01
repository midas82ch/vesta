# ADR 0008: Administrierbarer Angebotskatalog und explizites Kein-Treffer-Ergebnis

- Status: angenommen
- Datum: 2026-09-01

## Kontext

Kategorien und Angebotszuordnungen waren bisher durch Seed-Dateien und den
Quellenimport vorgegeben. Fachliche Korrekturen erforderten damit eine
Codeänderung. Angebote konnten im Adminbereich zwar kontrolliert, aber weder
vollständig manuell erfasst noch einem anderen Bedarf zugeordnet werden. Ein
leeres Matching-Ergebnis wurde zudem wie eine menschliche Weiterleitung
behandelt, obwohl „kein aktuelles Angebot gefunden“ ein eigenständiges und
zulässiges Ergebnis ist.

## Entscheid

### 1. Revisionierter Kategorie- und Angebotskatalog

Kategorien werden in `need_definitions` und `need_localizations` gepflegt. Sie
besitzen Status, Sortierung, kontrolliertes Symbol, Revisionsnummer und Texte
für alle sechs unterstützten Sprachen. Nur veröffentlichte Kategorien werden
öffentlich und für neue Angebotszuordnungen angeboten. Eine Kategorie mit
bestehendem Mapping kann nicht archiviert werden.

Angebote können im Adminbereich als Entwurf erfasst, Kategorien zugeordnet und
in einem separaten Schritt veröffentlicht oder archiviert werden. Schreibende
Operationen verwenden optimistische Revisionsprüfungen. Jede Änderung wird mit
Adminname, Vorher-/Nachher-Stand und Zeitpunkt in `admin_change_log`
protokolliert.

### 2. Manuelle Übernahme schützt vor Import-Überschreibung

`offers.management_mode` unterscheidet quellengeführte (`source`) von manuell
geschützten (`manual`) Angeboten. Der automatische Import aktualisiert Felder,
Kategorien und Verifikation nur bei quellengeführten Angeboten. Ein weiterhin
erfolgreich geprüftes, aber manuell geschütztes Angebot erzeugt nur einen
Importlauf; sein redaktioneller Stand bleibt unverändert.

Der Singleton `offer_import_settings` steuert geplante und manuell gestartete
Importjobs. Ein deaktivierter Job beendet sich erfolgreich ohne Datenänderung
und protokolliert `skipped_disabled`. Der Schalter ist revisioniert und wird im
Änderungsprotokoll erfasst.

### 3. Getrennte Datenbankrolle und Desktop-Admin

Schreibende Katalogendpunkte verwenden die eingeschränkte Rolle
`vesta_admin`. `vesta_app` bleibt auf lesende Katalogzugriffe beschränkt und
`vesta_ingest` kann die Importsteuerung nur lesen. Der Adminbereich ist ein
internes, desktop-orientiertes Werkzeug mit breiten Tabellen und Mapping-
Matrix; Tastaturbedienung und robuste Darstellung bleiben erforderlich, eine
eigene mobile Admin-Nutzerführung jedoch nicht.

### 4. Kein Treffer ist keine Sicherheits-Weiterleitung

Die öffentlichen Antworten unterscheiden `matches`, `no_match` und `handoff`.
Ein leeres, reguläres Matching liefert `no_match` und eine verständliche
Leermeldung. `handoff` ist für Sicherheitsregeln und ausdrückliche fachliche
Weiterleitungsgründe reserviert.

## Konsequenzen

- Fachpersonen können Kategorien, Mapping und Angebote ohne Deployment
  pflegen; veröffentlichte Inhalte bleiben dennoch kontrolliert.
- Importierte Angebote werden standardmässig weiterhin automatisch gepflegt.
  Nach einer manuellen Übernahme liegt die Verantwortung für Aktualität und
  erneute Verifikation beim Admin.
- Kategorien werden nicht hart gelöscht. Dadurch bleiben historische
  Zuordnungen und Änderungsspuren nachvollziehbar.
- Quellenkonfiguration, frei definierbare Feldmappings, Dublettenerkennung und
  Importvorschau bleiben ein eigener späterer Ausbau; ADR 0008 betrifft das
  bestehende Kategorie-Mapping und die operative Importsteuerung.
