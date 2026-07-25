# ADR 0001: Modularer Monolith für den Pilot

- Status: angenommen
- Datum: 2026-07-25

## Kontext

Der Pilot muss fachliche Annahmen und Datenqualität testen. Komplexe verteilte
Infrastruktur würde die Lernzyklen verlängern und löst derzeit kein belegtes
Skalierungsproblem.

## Entscheid

Vesta startet als Monorepo mit zwei auslieferbaren Anwendungen:

- Next.js-Webanwendung
- modulare FastAPI-Anwendung

Matching, Sicherheitsregeln und Datenzugriff bleiben innerhalb der API klar
getrennte Module. PostgreSQL ist die einzige Betriebsdatenbank.

## Konsequenzen

- Ein lokaler Stack und eine gemeinsame Versionshistorie
- Fachlogik kann ohne Netzwerk und Sprachmodell getestet werden
- Spätere Extraktion einzelner Komponenten bleibt möglich
- Schnittstellen werden versioniert, obwohl noch keine Microservices bestehen
