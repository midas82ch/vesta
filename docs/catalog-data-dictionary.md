# Datenwörterbuch für Bedarf und Leistungen

Dieses Wörterbuch grenzt die öffentlich sichtbaren Bereiche und die harten
Leistungsmerkmale ab. Ein Merkmal darf einem Angebot nur mit Quellenbeleg oder
dokumentierter Bestätigung der Institution zugeordnet werden.

## Hauptbereiche

| Schlüssel | Öffentliche Bedeutung | Nicht automatisch eingeschlossen |
|---|---|---|
| `sleep_tonight` | Ein Schlafplatz für die nächste Nacht | Tagesaufenthalt oder allgemeine Beratung |
| `basic_needs` | Konkrete alltägliche Grundversorgung | Jede Stelle, die gelegentlich Getränke oder Essen abgibt |
| `counselling` | Beratung zu einem bestimmten Thema | Reine Aufenthalts- oder Verpflegungsangebote |
| `victim_support` | Hilfe nach Gewalt, Drohung oder Straftat | Allgemeine Krisenberatung ohne Opferhilfeauftrag |
| `daytime_stay` | Aufenthalt und Toilettenzugang ohne Konsumzwang | Kommerzielle Orte ohne bestätigten niederschwelligen Zugang |

## Grundversorgung

| Schlüssel | Bedeutung | Abgrenzungsbeispiel |
|---|---|---|
| `meal` | Fertige Mahlzeit | Keine allgemeine Lebensmittelabgabe |
| `groceries` | Lebensmittel zum Mitnehmen | Keine einzelne Mahlzeit als Beleg |
| `shower` | Nutzbare Dusche | Waschgelegenheit allein reicht nicht |
| `laundry` | Wäsche waschen | Keine reine Kleiderabgabe |
| `clothing` | Kleider oder gezielte Kleiderhilfe | Hygieneartikel allein reichen nicht |
| `toilet` | Bestätigter Toilettenzugang | Nur bei tatsächlich offenem Zugang |
| `locker` | Schliessfach oder Gepäckaufbewahrung | Keine allgemeine Postadresse |

## Beratung

| Schlüssel | Bedeutung | Abgrenzungsbeispiel |
|---|---|---|
| `general_social` | Allgemeine Sozialberatung und Triage | Kein reiner Treffpunkt |
| `housing` | Beratung zu Wohnen und Obdach | Nicht automatisch ein Schlafplatz |
| `finances` | Geld, Budget oder Schulden | Keine allgemeine Sozialberatung ohne Beleg |
| `health` | Somatische Gesundheit | Psychische Krise ist ein eigenes Merkmal |
| `mental_health` | Psychische Belastung oder Krise | Kein medizinischer Notfall; dafür gilt 144 |
| `legal` | Rechtliche Beratung | Administrative Hilfe allein reicht nicht |
| `addiction` | Fachliche Suchtberatung | Eine suchtbezogene Zielgruppe allein reicht nicht |

## Suchtpräzisierung

| Schlüssel | Bedeutung |
|---|---|
| `addiction_alcohol` | Alkoholbezogene Hilfe ist ausdrücklich belegt |
| `addiction_opioids` | Opioid-/Heroinhilfe ist ausdrücklich belegt |
| `addiction_other` | Andere einzelne Substanzen |
| `addiction_multiple` | Mehrfachkonsum beziehungsweise mehrere Substanzen |
| `addiction_unsure` | Die Person ist nicht sicher; dies ist kein Leistungsbeleg und kein harter Filter |

## Statusfelder

- Leistungsstatus `confirmed`: Quelle oder Institution bestätigt das Merkmal.
- Leistungsstatus `draft`: Importvorschlag; nicht für öffentliches Matching.
- Zustimmung `approved`: dokumentierter Umfang der Zustimmung liegt vor.
- Zustimmung `legacy_pending`: bestehender Eintrag während der maximal
  90-tägigen Klärungsfrist.
- Zustimmung `pending` oder `declined`: keine öffentliche Ausgabe.
- Prüfung `current`: Ablaufdatum liegt in der Zukunft.
- Prüfung `overdue_grace`: höchstens 30 Tage abgelaufen; Ausgabe nur mit
  Abklärungshinweis.
- Prüfung `expired`: länger abgelaufen; keine öffentliche Ausgabe.
