# ADR 0002: Deterministische Sicherheit und Vermittlung

- Status: angenommen
- Datum: 2026-07-25

## Kontext

Generative Modelle können Eingaben übersetzen und vereinfachen, sind aber keine
verlässliche Instanz für Notfallhandlungen oder den Zugang zu knappen Hilfen.

## Entscheid

- Sicherheitsregeln laufen vor Dialog- und Matching-Funktionen.
- Harte Zugangskriterien werden versioniert und deterministisch ausgewertet.
- Das Sprachmodell darf nur strukturierte Anfragen vorbereiten und geprüfte
  Ergebnisse erklären.
- Jede Empfehlung enthält Datenquelle und Aktualitätsstatus.
- Unsicherheit führt zu transparenter Abklärung oder menschlicher Übergabe.

## Konsequenzen

Die Kernvermittlung bleibt auch ohne AI funktionsfähig und testbar. Neue Regeln
benötigen fachliche Freigabe und Regressionstests.
