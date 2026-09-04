# ADR 0002: Deterministische Sicherheit und Vermittlung

- Status: angenommen
- Datum: 2026-07-25

## Kontext

Generative Modelle können Eingaben übersetzen und vereinfachen, sind aber keine
verlässliche Instanz für Notfallhandlungen oder den Zugang zu knappen Hilfen.

## Entscheid

- Sicherheitsregeln laufen vor Dialog- und Matching-Funktionen.
- Harte Zugangskriterien werden versioniert und deterministisch ausgewertet.
- Das Sprachmodell darf strukturierte Anfragen vorbereiten und freigegebene
  Fragen formulieren. Öffentliche Ergebnisbegründungen werden nicht generiert.
- Jede Empfehlung führt, sofern vorhanden, direkt zur geprüften
  Angebotsseite; technische Quellen- und Aktualitätsprüfungen bleiben im
  Audit.
- Unsicherheit führt zu transparenter Abklärung oder menschlicher Übergabe.

## Konsequenzen

Die Kernvermittlung bleibt auch ohne AI funktionsfähig und testbar. Neue Regeln
benötigen fachliche Freigabe und Regressionstests.
