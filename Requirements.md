# Vesta – nächste Anforderungen

## Ziel

Der bestehende klickfähige Prototyp wird in zwei Bereichen weiterentwickelt:

1. übersichtliche, vertrauenswürdige und mobil gut bedienbare Oberfläche;
2. kontrollierter Admin-Prozess für Import, Mapping und Veröffentlichung von Angeboten.

## Layout und Nutzerführung

- Die Startseite bleibt schlank und führt unmittelbar zum passenden Angebot.
- Ergebnisse zeigen höchstens drei priorisierte Angebote mit verständlicher
  Beschreibung und direkten Kontakt- beziehungsweise Weglinks.
- Im Freitext genannte Themen werden mehrsprachig und deterministisch mit den
  geprüften Angebotstexten abgeglichen und beeinflussen die Priorisierung.
- AI-, Matching-, Quellen- und Statusbegründungen werden nicht öffentlich
  angezeigt; die vollständige technische Spur bleibt im Admin-Audit.
- Inhalt, visuelle Hierarchie, Abstände und Typografie werden vereinheitlicht.
- Der Dialog ist auf Mobilgeräten ebenso verständlich und bedienbar wie auf Desktop.
- Lade-, Fehler-, Leer- und Erfolgszustände sind klar erkennbar.
- Eine freiwillige Standortfreigabe sortiert gleich geeignete Angebote nach
  ungefährer Luftliniendistanz; ohne Freigabe bleibt die Suche vollständig
  nutzbar.
- Angebote mit verifizierter Adresse zeigen diese und einen externen Link zur
  Wegbeschreibung. Eine Distanz wird nur bei vorhandenen Koordinaten angezeigt.
- Barrierefreiheit, Mehrsprachigkeit und PWA-Funktion bleiben erhalten.
- Erklärende Inhalte bleiben in separaten Bereichen wie Impressum und Datenschutz.

## Admin-Bereich für Angebote

Nur berechtigte Admins dürfen Quellen, Importe, Mappings und Veröffentlichungen verwalten.

Der Adminbereich ist ein internes, desktop-orientiertes Arbeitswerkzeug. Auf
kleineren Browserfenstern darf er nicht unbedienbar werden; eine eigenständige
mobile Admin-Nutzerführung ist jedoch keine Anforderung.

### Kategorien und Angebots-Mapping

- Kategorien können im Adminbereich neu als Entwurf angelegt, übersetzt,
  sortiert und veröffentlicht werden.
- Jede Kategorie besitzt eine kontrollierte Symbolzuordnung und vollständige
  Texte für Deutsch, Französisch, Englisch, Spanisch, Portugiesisch und Darija.
- Die Zuordnung zwischen Kategorien und Angeboten ist als Matrix sichtbar und
  kann ohne Codeänderung bearbeitet werden.
- Kategorien mit zugeordneten Angeboten dürfen nicht archiviert werden.
- Neue oder geänderte Kategorien erscheinen erst nach ihrer Veröffentlichung
  in der öffentlichen Bedarfsauswahl.

### Manuelle Angebote

- Angebote können vollständig manuell erfasst und bestehenden
  veröffentlichten Kategorien zugeordnet werden.
- Manuell erfasste Angebote beginnen immer als Entwurf und werden erst nach
  einem separaten Freigabeschritt öffentlich sichtbar.
- Importierte Angebote können im Adminbereich übernommen und manuell geschützt
  werden; nachfolgende automatische Importe überschreiben weder ihre Felder
  noch ihr Kategorie-Mapping oder ihre manuelle Verifikation.
- Bearbeitungen und Statuswechsel verwenden Revisionsnummern gegen
  versehentliches gegenseitiges Überschreiben und werden protokolliert.

### Kein passendes Angebot

- Ein leeres Matching-Ergebnis ist ein reguläres fachliches Ergebnis und wird
  öffentlich ausdrücklich als „aktuell kein passendes Angebot“ angezeigt.
- Eine menschliche Notfall-Weiterleitung bleibt davon getrennt und wird nur
  durch Sicherheitsregeln ausgelöst.

### Opferhilfe und Sicherheitsdialog

- `victim_support` ist eine eigene Bedarfskategorie mit Texten in Deutsch,
  Französisch, Englisch, Spanisch, Portugiesisch und Darija.
- Hinweise auf Gewalt, Drohungen oder akute Gefahr werden vor jedem AI-Aufruf
  durch versionierte Regeln erkannt.
- Bei unmittelbarer Gefahr werden ausschließlich 117 und 144 angeboten; in
  allen anderen Sicherheitsfällen 142 und geprüfte Opferhilfe-Angebote.
- Bei altersbeschränkten verbleibenden Angeboten wird das konkrete Alter, nie
  das Geburtsdatum, erfragt. Es wird nur in der laufenden Dialogsession
  verarbeitet und weder an AI noch an Audit, Log oder Export übergeben.
- Unbekannte und abgelehnte Angaben bleiben sichtbar und führen zu einer
  Abklärungsunsicherheit statt zu einem stillen Ausschluss.

### Präzise Bedarfsauswahl

- Die fünf Hauptbereiche sind Schlafplatz, Grundversorgung, Beratung,
  Opferhilfe sowie Aufenthalt & Toilette.
- Grundversorgung und Beratung werden vor dem Matching mit grossen,
  beschrifteten Icon-Kacheln präzisiert; bei Sucht folgt ein zweiter kurzer
  Schritt für Alkohol, Opioide/Heroin, andere oder mehrere Substanzen.
- Die mobile Ansicht zeigt bei 320 bis 480 Pixel Breite zwei Kacheln pro Zeile
  ohne horizontales Scrollen. Auswahlzustand, Häkchen und `aria-pressed`
  funktionieren mit Touch, Tastatur und Screenreader.
- Bestätigte Leistungen sind harte Matching-Kriterien. Eine beiläufig
  erwähnte Mahlzeit macht ein Angebot nicht zur allgemeinen
  Grundversorgungsstelle.
- Freitext darf geeignete Kacheln vorauswählen; die Person bestätigt sie vor
  dem Matching.
- Höchstens drei unterschiedliche fachlich passende Angebote werden gezeigt.
  Fehlt ein belegter Treffer, wird `no_match` statt einer unpassenden
  Alternative geliefert.

### Institutionelle Freigabe und Aktualität

- Jedes Leistungsmerkmal benötigt eine Primärquelle oder dokumentierte
  Bestätigung der Institution.
- Neue Angebote werden erst nach dokumentierter institutioneller Zustimmung
  veröffentlicht. Bestehende Einträge dürfen höchstens 90 Tage als
  `legacy_pending` weiterlaufen.
- Angebotsprüfungen unterscheiden `current`, `overdue_grace` und `expired`.
  Nach Ablauf bleibt ein Angebot höchstens 30 Tage mit
  „Bitte vorher abklären“ sichtbar; danach wird es ausgeblendet.
- Quellenimporte speichern fachliche Änderungen als revisionssicheren
  Entwurf. Sie beschädigen oder überschreiben die veröffentlichte Fassung
  nicht automatisch.

### Quellen und Import

- Quellen anlegen, bearbeiten, aktivieren und deaktivieren.
- Importe manuell starten und zeitgesteuert ausführen.
- Importstatus, Laufzeit, Quelle und Ergebnis anzeigen.
- Neue, geänderte, unveränderte und fehlerhafte Datensätze unterscheiden.
- Fehlgeschlagene Importe nachvollziehbar wiederholen können.
- Der automatische Import kann im Adminbereich zentral ein- und ausgeschaltet
  werden. Ein deaktivierter geplanter Lauf wird als übersprungen protokolliert;
  bestehende Angebote bleiben unverändert.
- Einzelne HTTPS-URLs können unabhängig vom Automatikschalter als persistente
  Importaufträge erfasst und bei vorübergehenden Fehlern wiederholt werden.
- URL-Abrufe blockieren private und reservierte IPv4-/IPv6-Ziele, prüfen jedes
  Redirect-Ziel, beachten `robots.txt` und begrenzen Zeit sowie Datenmenge.
- Extraktion und Übersetzungen erzeugen nur unveröffentlichte Entwürfe;
  vollständiges HTML wird nicht gespeichert.

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
- Angebotstexte werden getrennt in sechs Sprachfassungen gepflegt.
  Maschinenentwürfe dürfen erst nach expliziter Prüfung veröffentlicht werden.
- Fehlt eine geprüfte Übersetzung, wird die geprüfte deutsche Fassung mit einem
  lokalisierten Fallback-Hinweis angezeigt.

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
- Der Browser fragt den Standort nur nach einem ausdrücklichen Klick ab.
- Standort und konkrete Distanzen werden weder dauerhaft gespeichert noch an
  das AI-Modell oder den Audit-Log übermittelt.
- Fachliche Eignung bleibt vor Nähe priorisiert. Ein fehlender Standort ist
  kein Ausschlussgrund; bei gleicher Eignung kann ein Angebot jedoch hinter
  näheren Angeboten außerhalb der öffentlichen Dreierauswahl liegen.
