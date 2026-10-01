# ADR 0011: Icon-basierte Leistungsauswahl und Katalog-Governance

- Status: angenommen
- Datum: 2026-10-01

## Kontext

Die bisherigen Hauptkategorien waren für eine zuverlässige Vermittlung zu
breit. Eine erwähnte Mahlzeit konnte ein spezialisiertes Angebot fälschlich
als allgemeine Grundversorgung erscheinen lassen. Allgemeine Suchtberatung
war nicht präzise genug, um etwa ein belegtes Opioidangebot von einem
alkoholspezifischen Treffpunkt zu unterscheiden. Alterszugänge wie 14–23
lassen sich zudem nicht mit einer reinen Frage «ab 18» entscheiden.

Eine klassische Mehrfachauswahl mit kleinen Kontrollkästchen wäre auf dem
Smartphone unnötig technisch. Gleichzeitig dürfen importierte Angaben oder
eine blosse Aufnahme in eine Kandidatenliste nicht automatisch zur
Veröffentlichung führen.

## Entscheid

1. Vesta führt fünf Hauptbereiche: Schlafplatz, Grundversorgung, Beratung,
   Opferhilfe sowie Aufenthalt & Toilette.
2. Grundversorgung und Beratung werden vor dem Matching mit grossen,
   beschrifteten Icon-Kacheln präzisiert. Intern ist dies `multi_choice` mit
   `presentation=icon_grid`; die technische Bezeichnung ist öffentlich nie
   sichtbar. Sucht erhält einen zweiten kurzen Präzisierungsschritt.
3. Bestätigte Leistungsmerkmale sind harte Filter. Ein Angebot ohne
   quellenbelegtes Merkmal gilt nicht als Ersatz. Fehlt ein bestätigter
   Treffer, liefert Vesta `no_match`.
4. Ein konkretes Alter wird nur abgefragt, wenn ein verbleibendes Angebot eine
   Altersregel besitzt. Es lebt ausschliesslich im Arbeitsspeicher der
   Dialogsession, wird nicht an AI übergeben und nicht in Audit, Logs oder
   Export geschrieben. Im Audit erscheint nur das Prüfergebnis.
5. Fachliche Eignung wird vor Standort und Distanz geprüft. Öffentlich werden
   höchstens drei unterschiedliche passende Angebote ausgegeben.
6. Neue oder importierte Angebote und Leistungsmerkmale sind Entwürfe. Für
   eine Veröffentlichung braucht es Quellenbelege, eine aktuelle Prüfung und
   eine dokumentierte Zustimmung der Institution.
7. Bestehende Einträge können für höchstens 90 Tage als `legacy_pending`
   weiterlaufen. Eine abgelaufene Angebotsprüfung hat eine 30-tägige
   Warnfrist (`overdue_grace`) mit dem Hinweis «Bitte vorher abklären»;
   danach ist das Angebot `expired` und öffentlich unsichtbar.
8. Ein Quellenimport speichert eine revisionssichere Gegenüberstellung, ändert
   aber keine bereits veröffentlichte fachliche Fassung automatisch.

## Konsequenzen

- Die öffentliche Auswahl benötigt einen zusätzlichen, aber kurzen Schritt.
  Sie bleibt durch grosse Touch-Ziele, sichtbare Texte, `aria-pressed` und
  Tastaturbedienung niederschwellig.
- Die Trefferzahl kann sinken. Ein ehrlicher Leertreffer ist fachlich besser
  als eine unpassende Weiterleitung und kann kontextbezogene Hilfewege wie
  147 oder 143 anbieten.
- Der Katalog benötigt mehr redaktionelle Arbeit: Leistungsmerkmale,
  Quellenbelege, Zustimmungen und Prüfungen werden explizit gepflegt.
- Kandidaten aus «Uf dr Gass» oder anderen Verzeichnissen sind keine
  automatischen Veröffentlichungsfreigaben.
- `is_adult` bleibt während einer Übergangsrelease lesbar; der öffentliche
  Dialog verwendet bei relevanten Altersregeln das konkrete Alter.
