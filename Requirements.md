# Vesta – nächste Anforderungen

## Ziel

Der bestehende klickfähige Prototyp wird in zwei Bereichen weiterentwickelt:

1. übersichtliche, vertrauenswürdige und mobil gut bedienbare Oberfläche;
2. kontrollierter Admin-Prozess für Import, Mapping und Veröffentlichung von Angeboten.

## Layout und Nutzerführung

- Die Startseite bleibt schlank und führt unmittelbar zum passenden Angebot.
- Inhalt, visuelle Hierarchie, Abstände und Typografie werden vereinheitlicht.
- Der Dialog ist auf Mobilgeräten ebenso verständlich und bedienbar wie auf Desktop.
- Lade-, Fehler-, Leer- und Erfolgszustände sind klar erkennbar.
- Barrierefreiheit, Mehrsprachigkeit und PWA-Funktion bleiben erhalten.
- Erklärende Inhalte bleiben in separaten Bereichen wie Impressum und Datenschutz.

## Admin-Bereich für Angebote

Nur berechtigte Admins dürfen Quellen, Importe, Mappings und Veröffentlichungen verwalten.

### Quellen und Import

- Quellen anlegen, bearbeiten, aktivieren und deaktivieren.
- Importe manuell starten und zeitgesteuert ausführen.
- Importstatus, Laufzeit, Quelle und Ergebnis anzeigen.
- Neue, geänderte, unveränderte und fehlerhafte Datensätze unterscheiden.
- Fehlgeschlagene Importe nachvollziehbar wiederholen können.

### Mapping und Datenqualität

- Externe Felder auf das Vesta-Datenmodell abbilden.
- Werte normalisieren, beispielsweise Kategorien, Sprachen und Verfügbarkeiten.
- Pflichtfelder und Datentypen vor der Übernahme validieren.
- Dubletten erkennen und zur Prüfung markieren.
- Unbekannte oder nicht zuordenbare Werte sichtbar machen und manuell korrigieren.
- Eine Vorschau zeigt die Auswirkungen eines Mappings vor dem Import.

### Prüfung und Veröffentlichung

- Importierte Angebote werden zunächst als Entwurf gespeichert.
- Ein Admin kann Änderungen prüfen, korrigieren, freigeben oder verwerfen.
- Angebote werden erst nach ausdrücklicher Freigabe veröffentlicht.
- Quelle, Prüfzeitpunkt, prüfende Person und Datenqualität bleiben am Angebot sichtbar.
- Jede Änderung und Veröffentlichung wird in einer Historie protokolliert.

## Sicherheits- und Betriebsanforderungen

- Admin-Funktionen erfordern Authentifizierung und rollenbasierte Berechtigungen.
- Zugangsdaten und API-Schlüssel werden nicht im Quellcode oder Importprotokoll gespeichert.
- Importfehler dürfen bestehende veröffentlichte Angebote nicht beschädigen.
- Import und Veröffentlichung müssen reproduzierbar und nachvollziehbar sein.
- Personenbezogene Daten werden weder benötigt noch absichtlich importiert.

## Akzeptanzkriterien für den nächsten Prototyp

- Ein Admin kann eine Quelle konfigurieren und einen Testimport starten.
- Das Feldmapping kann ohne Codeänderung erstellt und gespeichert werden.
- Vor der Übernahme ist eine verständliche Importvorschau verfügbar.
- Fehler und Dubletten können einzeln bearbeitet werden.
- Ein geprüftes Angebot kann veröffentlicht werden und erscheint anschließend im öffentlichen Matching.
- Importlauf, Mapping und Freigabe sind in der Historie nachvollziehbar.
- Die öffentliche Oberfläche funktioniert responsiv, barrierearm und in allen unterstützten Sprachen.
