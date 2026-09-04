# ADR 0009: Deterministische Opferhilfe und geprüfte URL-Importe

- Status: angenommen
- Datum: 2026-09-02

## Kontext

Der öffentliche Dialog kann Hinweise auf Gewalt, Drohungen oder Straftaten
enthalten. Solche Hinweise dürfen weder von der Verfügbarkeit eines
Sprachmodells noch von einer probabilistischen Klassifikation abhängen. Zudem
fehlte bisher ein kontrollierter Weg, ein einzelnes Hilfsangebot ausgehend von
einer URL zu erfassen, in alle unterstützten Sprachen zu übertragen und vor
der Veröffentlichung fachlich zu prüfen.

Die bisherige Zahlenfrage zum Alter erhob mehr Daten als für die im Pilot
verwendeten Zugangsregeln erforderlich. Für die Entscheidung über Angebote ab
18 genügt eine bestätigte Ja-/Nein-Angabe.

## Entscheid

### 1. Sicherheit vor AI und Matching

Ein versionierter, deterministischer Detektor prüft Freitext in Deutsch,
Französisch, Englisch, Spanisch, Portugiesisch und Darija vor jedem AI-Aufruf.
Ein Treffer führt in die nicht-generative Frage nach unmittelbarer Gefahr.
Bei bestätigter unmittelbarer Gefahr werden ausschließlich 117 und 144
angezeigt. In allen anderen Antwortzuständen werden 142 und geprüfte Angebote
der Kategorie `victim_support` ausgegeben. Der Sicherheitsentscheid und sein
Grundcode werden im Workflow-Audit festgehalten.

### 2. Minimierte Altersangabe

Der öffentliche Dialog verwendet `person.is_adult` und fragt ausschließlich,
ob die hilfesuchende Person 18 Jahre oder älter ist. Unbekannte und abgelehnte
Angaben bleiben als eigene Zustände erhalten. Sie führen zu einer sichtbaren
Zugangsunsicherheit, nicht zu einem stillen Ausschluss. Andere Altersgrenzen
als genau 18 werden weiterhin als direkt zu klärende Bedingung behandelt.

### 3. Geprüfte Angebotsübersetzungen

Angebotstexte werden je Sprache in `offer_localizations` geführt. Maschinell
erzeugte Fassungen beginnen als `machine_draft`. Öffentlich erscheinen nur
`reviewed`-Fassungen; fehlt eine geprüfte Zielsprache, wird die geprüfte
deutsche Fassung mit einem lokalisierten Hinweis verwendet. Angebots- und
Übersetzungssprache bleiben getrennte Konzepte.

### 4. Sicherer, persistenter URL-Import

Manuelle URL-Aufträge werden in `offer_import_jobs` persistiert und von einer
eigenen Worker-Rolle verarbeitet. Der Abruf akzeptiert ausschließlich HTTPS
auf Port 443, validiert DNS und jedes Redirect-Ziel, blockiert nicht-öffentliche
IPv4-/IPv6-Adressen, beachtet `robots.txt` und begrenzt Zeit, Redirects und
Datenmenge. Vollständiges HTML wird nicht gespeichert. AI-Extraktion und
Übersetzung erzeugen ausschließlich unveröffentlichte Entwürfe mit kurzen
Quellenbelegen; fehlende Angaben dürfen nicht erfunden werden.

Neue Kategorien beginnen als Entwurf. Sie können bereits Entwurfsangeboten
zugeordnet werden, werden aber erst veröffentlicht, wenn mindestens ein
zugeordnetes Angebot eine aktuelle Prüfung und eine geprüfte deutsche Fassung
besitzt. Angebote können ihrerseits erst veröffentlicht werden, wenn alle
zugeordneten Kategorien veröffentlicht sind.

## Konsequenzen

- Sicherheitsrouting funktioniert auch bei vollständigem AI-Ausfall.
- Der öffentliche Dialog erhebt keine konkrete Alterszahl mehr.
- Maschinelle Übersetzungen gelangen nicht ungeprüft in die öffentliche Suche.
- URL-Importe bleiben manuell startbar, wenn der geplante Katalogimport
  deaktiviert ist.
- Der Worker darf neue Entwürfe anlegen, aber bestehende Angebote weder ändern
  noch löschen. Dubletten werden zur manuellen Prüfung markiert.
- Die Kategorie Opferhilfe bleibt in PostgreSQL zunächst ein Entwurf. Ihre
  Arbeitsübersetzungen und die ersten Quellen müssen vor der Veröffentlichung
  fachlich geprüft werden.
