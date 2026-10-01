# Szenariomatrix Dialog und Matching

Die Matrix enthält anonymisierte fachliche Regressionen. Sie enthält keine
Rohtranskripte und keine konkreten Alterswerte aus realen Abfragen.

| Szenario | Erwarteter Dialog | Erwartetes Ergebnis |
|---|---|---|
| Grundversorgung allgemein | Icon-Auswahl erscheint | Noch kein Matching vor bestätigter Leistung |
| Mahlzeit | «Mahlzeit» bestätigt | Nur Angebote mit `meal=confirmed` |
| Dusche und Wäsche | beide Kacheln gewählt | Nur Angebote mit beiden bestätigten Leistungen |
| Beratung allgemein | Beratungs-Icon-Auswahl erscheint | Thema wird vor dem Matching präzisiert |
| Opioidberatung | Sucht, danach Opioide/Heroin | Kein La Gare ohne bestätigte Opioidleistung |
| Gassenarbeit, passendes Beratungsthema | passendes Thema bestätigt | Gassenarbeit ist bei aktueller Prüfung und Zustimmung auffindbar |
| Schlafplatz mit Altersregel | konkrete Altersfrage nur bei Relevanz | Pluto nur innerhalb seiner belegten Altersgrenze |
| Minderjährige Person ohne Schlafangebot | kein fachlicher Treffer | `no_match`, 147 als primärer Hilfeweg |
| Psychische Krise ohne Treffer | regulärer Leertreffer | `no_match`, 143 mit kurzer Erklärung |
| Gewalt, keine unmittelbare Gefahr | deterministischer Sicherheitsdialog | 142 und ausschliesslich Opferhilfe-Angebote |
| Unmittelbare Gefahr | deterministischer Sicherheitsdialog | 117 und 144, kein reguläres Matching |
| Aufenthalt ohne Konsumzwang | direkte Hauptkategorie | Nur bestätigte geeignete Aufenthaltsorte |
| Abgelaufene Prüfung innerhalb 30 Tagen | keine zusätzliche Frage | sichtbar mit «Bitte vorher abklären» |
| Prüfung länger als 30 Tage abgelaufen | keine zusätzliche Frage | Angebot ausgeschlossen |
| Kein bestätigtes Leistungsmerkmal | keine Ersatzempfehlung | `no_match` |

## Erkenntnisse aus den September-Prüfungen

Die anonymisierte Auswertung der Abfragen vom 13. bis 15. September zeigte
drei wiederkehrende Ursachen: zu breite Hauptkategorien, fehlende oder falsch
generalisierte Leistungsmerkmale und Altersregeln, die mit «ab 18» nicht
abbildbar sind. Daraus folgen die Icon-Präzisierung, harte belegte
Leistungsfilter und die flüchtige konkrete Altersprüfung. Einzelne Eingaben,
vollständige Dialogtexte und Zahlenwerte werden nicht in diesem Repository
dokumentiert.
