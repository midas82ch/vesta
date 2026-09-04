# Hosting-Empfehlung

Stand: 2026-07-25

## Empfehlung

Für Vesta wird Exoscale in der Schweizer Zone `ch-dk-2` (Zürich) empfohlen.
Exoscale betreibt Schweizer Zonen in Zürich und Genf. Managed PostgreSQL ist in
den Zonen verfügbar und unterstützt die für Vesta vorgesehenen Erweiterungen
PostGIS und pgvector.

Die Empfehlung verbindet:

- Datenhaltung in der Schweiz
- Schweizer Vertragspartner
- offene Standards und überschaubaren Anbieter-Lock-in
- Managed PostgreSQL mit Backups und Hochverfügbarkeitsoptionen
- Managed Kubernetes für einen späteren belastbaren Feldbetrieb

## Zieltopologie

### Technischer Prototyp

```text
Internet
   |
eine Exoscale Compute-Instanz
   +-- Web-Container
   +-- API-Container
   +-- URL-Import-Worker (separate DB-Rolle)
   |
Exoscale Managed PostgreSQL
```

Diese Topologie ist günstig und genügt für interne Tests mit Demo- oder
öffentlichen Angebotsdaten. Sie ist nicht hochverfügbar.

### Feldpilot

```text
Internet
   |
Network Load Balancer
   |
Exoscale SKS Pro in ch-dk-2
   +-- mindestens zwei Web-Replikate
   +-- mindestens zwei API-Replikate
   +-- mindestens ein URL-Import-Worker
   |
Managed PostgreSQL mit geeigneter Redundanz- und Backup-Stufe
   |
Object Storage für verschlüsselte technische Artefakte
```

Die Anwendung bleibt als Container portabel. Infrastruktur und Deployments
werden vor dem Feldpilot mit Terraform und einer CI/CD-Pipeline reproduzierbar
gemacht.

## Alternative: AWS Zürich

AWS `eu-central-2` ist die beste Alternative, wenn bereits AWS-Kompetenz,
Verträge und Governance vorhanden sind:

- ECS/Fargate für Web und API
- RDS for PostgreSQL mit PostGIS und pgvector
- Application Load Balancer, ECR, KMS, Secrets Manager und CloudWatch

Die Region Zürich umfasst drei Availability Zones. Datenschutz, Subprozessoren
und allfällige extraterritoriale Zugriffsrisiken müssen mit den beteiligten
öffentlichen und sozialen Organisationen ausdrücklich geklärt werden.

## OpenShift

OpenShift wird nur empfohlen, wenn eine Partnerorganisation bereits einen
betreuten Cluster, Betriebsprozesse und Support bereitstellt. Ein eigener
OpenShift-Cluster erzeugt für zwei Anwendungen und eine Datenbank
unverhältnismässigen Lizenz-, Infrastruktur- und Betriebsaufwand.

## Vor jedem Feldtest

Der konkrete Anbieterentscheid ist erst nach diesen Freigaben vollständig:

- Auftragsbearbeitungsvertrag und Liste der Subprozessoren
- verbindliche Standorte für Datenbank, Backups, Logs und Supportzugriffe
- Datenschutz-Folgenabschätzung
- Lösch-, Wiederherstellungs- und Incident-Prozess
- Verschlüsselung und Schlüsselverantwortung
- separate Prüfung eines späteren AI-/Sprachmodell-Anbieters
- Last-, Barrierefreiheits- und Ausfalltests

Die AI-Schnittstelle darf nicht stillschweigend Daten in eine andere Region
übertragen. Sie bleibt im MVP deaktiviert, bis Vertrag, Zweck und Datenfluss
freigegeben sind.

## Quellen

- [Exoscale Data Center Zones](https://community.exoscale.com/platform/dc-zones/)
- [Exoscale Managed PostgreSQL](https://www.exoscale.com/dbaas/postgresql/)
- [Exoscale SKS](https://community.exoscale.com/product/compute/containers/overview/)
- [AWS Region Zürich](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions.html)
- [RDS PostgreSQL Extensions](https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-extensions.html)
- [EDÖB: Datenschutz-Folgenabschätzung](https://www.edoeb.admin.ch/de/datenschutz-folgenabschaetzung)
- [EDÖB: Datenbearbeitung in der Cloud](https://www.edoeb.admin.ch/de/datenbearbeitung-in-der-cloud)
