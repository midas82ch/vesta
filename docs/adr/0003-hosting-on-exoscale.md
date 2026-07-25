# ADR 0003: Exoscale als bevorzugte Hosting-Plattform

- Status: vorgeschlagen
- Datum: 2026-07-25

## Kontext

Vesta verarbeitet perspektivisch Informationen über besonders vulnerable
Menschen. Schweizer Datenhaltung, transparente Unterauftragsverhältnisse,
Portabilität und geringer Betriebsaufwand sind deshalb wichtiger als ein sehr
breiter proprietärer Servicekatalog.

## Entscheid

Der Feldpilot soll bevorzugt in der Exoscale-Zone `ch-dk-2` betrieben werden:

- SKS Pro für die Anwendungscontainer
- Managed PostgreSQL mit PostGIS und pgvector
- Object Storage für technische Artefakte

AWS Zürich bleibt eine geprüfte Alternative. OpenShift wird nur auf einer
bereits von einer Partnerorganisation betriebenen Plattform eingesetzt.

## Konsequenzen

- Die Anwendungen bleiben OCI-Container und vermeiden anbieterspezifische APIs.
- Infrastruktur muss vor dem Feldpilot als Code ergänzt werden.
- Der konkrete Vertrag und die Datenschutz-Folgenabschätzung bleiben
  Freigabebedingungen.
- Die AI-Schnittstelle wird unabhängig vom Infrastruktur-Hosting bewertet.
