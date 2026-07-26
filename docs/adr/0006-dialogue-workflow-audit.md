# ADR 0006: Zusammenhängende Dialog-Workflow-Spur

- Status: angenommen
- Datum: 2026-07-27

## Kontext

ADR 0005 protokolliert einzelne Live-AI-Aufrufe mit Prompt und Antwort.
Damit lässt sich ein Provider-Aufruf technisch prüfen, aber nicht der
vollständige Dialog nachvollziehen: Benutzerantworten, deterministische
Frageauswahl und Matching-Entscheide sowie die tatsächlich ausgegebene
Antwort fehlen zwischen den AI-Einträgen.

Eine nachträgliche Rekonstruktion aus Prompt-Texten wäre unvollständig und
könnte die tatsächliche Reihenfolge falsch darstellen.

## Entscheid

Vesta führt zusätzlich `dialogue_workflow_log` mit drei nicht-AI-spezifischen
Stufen:

- `input`: Freitext, Bedarfsauswahl und Antworten der Person,
- `system`: validierte Interpretation, Frageauswahl und Matching-Ergebnis,
- `output`: das tatsächlich zurückgegebene öffentliche Antwortobjekt.

Der Interpretations-Endpunkt erzeugt eine zufällige Workflow-ID. Wenn daraus
ein Dialog gestartet wird, wird dieselbe ID als Dialog-Session-ID
weitergeführt. Direkte Bedarfsauswahlen erhalten wie bisher beim Start eine
neue zufällige Session-ID. AI-Einträge aus `ai_interaction_log` und
Workflow-Ereignisse werden im Admin-Endpunkt chronologisch zusammengeführt.

Schreibfehler der Workflow-Spur werden technisch protokolliert, dürfen aber
den öffentlichen Dialog genau wie Fehler des AI-Audit-Logs nicht verhindern.

## Konsequenzen

- Der Adminbereich zeigt den tatsächlichen Ablauf als
  Eingabe → AI → Systemlogik → AI → Antwort und kann bei längeren Dialogen
  zusätzliche Frage-/Antwortschritte dazwischen darstellen.
- Rohe Prompts und JSON bleiben pro Schritt verfügbar, sind in der
  Standardansicht aber eingeklappt.
- Eingaben, Systementscheide und Ausgaben werden wie die AI-Volltexte bis zur
  manuellen Löschung gespeichert. Der öffentliche Datenschutztext nennt
  diesen Umfang ausdrücklich.
- Historische AI-Einträge vor dieser Migration bleiben erhalten, besitzen
  aber keine nachträglich erfundene vollständige Workflow-Spur.
