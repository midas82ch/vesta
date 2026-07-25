# Mitwirken

## Grundsätze

- Keine realen Personendaten in Repository, Issues, Logs oder Testfixtures
- Keine Angebotsdaten ohne Quelle, Verantwortlichkeit und Ablaufdatum
- Keine generativen Entscheidungen über Zugang, Dringlichkeit oder Zuteilung
- Sicherheits- und Zugangsregeln benötigen Tests und fachliche Freigabe
- AI-generierte Texte bleiben als Entwurf erkennbar

## Änderungen prüfen

Web:

```bash
pnpm lint
pnpm typecheck
pnpm build
```

API:

```bash
cd apps/api
python -m ruff check --no-cache src tests
python -m unittest discover -s tests
```

## Angebotsdaten

Die Datei `data/seed/offers.example.json` enthält ausschliesslich
Demodatensätze. Reale Angebote sollen nicht direkt dort ergänzt werden. Für den
Feldpilot wird ein geprüfter Import- und Freigabeprozess gegen PostgreSQL
implementiert.

Eine Änderung fachlicher Zugangsbedingungen muss mindestens dokumentieren:

- wer die Information verantwortet
- aus welcher Quelle sie stammt
- wann sie geprüft wurde
- wann sie erneut geprüft werden muss
- welche Unsicherheit für Nutzende sichtbar bleibt
