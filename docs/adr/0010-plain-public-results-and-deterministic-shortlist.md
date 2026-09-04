# ADR 0010: Einfache öffentliche Ergebnisse und deterministische Auswahl

- Status: angenommen
- Datum: 2026-09-04

## Kontext

Die öffentliche Ergebnisansicht ersetzte die geprüfte Angebotsbeschreibung
durch eine generierte Erklärung des Matchings. Dadurch sahen hilfesuchende
Personen interne Formulierungen wie Quellen-, Sprach- und Statusprüfungen,
während die konkrete Leistung des Angebots in den Hintergrund trat.

Mit einem wachsenden Register können zudem mehrere Angebote dieselben
Grundkriterien erfüllen. Eine ungefilterte Gesamtliste ist für einen
niederschwelligen Zugang nicht hilfreich.

## Entscheid

- Öffentliche Dialogantworten enthalten keine generierte Ergebnisbegründung.
  AI bleibt für Freitextinterpretation und erlaubte Frageformulierungen
  verfügbar, entscheidet aber nicht über Auswahl oder Rang.
- Die öffentliche Oberfläche zeigt Name, kurze Beschreibung,
  Kontaktinformation, ungefähre Entfernung und direkte Handlungslinks.
- Technische Gründe, Unsicherheiten, Scores und ausgeschiedene Angebote
  bleiben im Workflow-Audit.
- Bestätigte Zugangskriterien werden deterministisch ausgewertet und tragen
  zur Rangfolge bei. Harte Konflikte schließen ein Angebot weiterhin aus.
- Wenn Freitext verwendet wird, erkennt eine kleine mehrsprachige,
  deterministische Begriffsliste Themen wie Sucht, Wohnen, Finanzen,
  Gesundheit oder Grundversorgung. Übereinstimmungen mit den geprüften
  Angebotstexten verbessern die Rangfolge, führen bei fehlender
  Übereinstimmung aber nicht zu einem harten Ausschluss.
- Fachliche Eignung bleibt vor Nähe priorisiert. Distanz löst nur Gleichstände
  gleich geeigneter Angebote.
- Der öffentliche Dialog zeigt höchstens die drei bestplatzierten Angebote.
  Weitere passende Treffer werden im Audit als lower_relevance_rank
  dokumentiert.
- Eine Rückfrage wird nur gestellt, wenn ihre Antwort eine Zugangsentscheidung
  tatsächlich verändern kann.

## Konsequenzen

Die Ergebnisansicht ist kürzer und handlungsorientiert. Ein Dialog verursacht
keine zusätzlichen AI-Kosten oder Wartezeit für Ergebnisbegründungen. Das
Matching bleibt vollständig testbar und im Adminbereich nachvollziehbar.

Sind Angebote anhand aller bekannten Kriterien gleichwertig und fehlt ein
Standort, bleibt der Angebotsname der stabile letzte Sortierschlüssel. Für
weitere fachliche Unterscheidungen muss die versionierte Begriffsliste
erweitert und mit realen Dialogfällen getestet werden.
