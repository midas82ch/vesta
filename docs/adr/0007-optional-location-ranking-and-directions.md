# ADR 0007: Freiwilliges Standort-Matching und Wegbeschreibung

- Status: angenommen
- Datum: 2026-07-27

## Kontext

Geeignete Angebote wurden bisher ausschliesslich nach fachlicher Eignung und
Name sortiert. Obwohl `offers.location` bereits als PostGIS-Geography
existiert, enthielten Domainmodell, Import und API keine Standortdaten.

Eine präzise oder dauerhafte Speicherung des Aufenthaltsorts einer
hilfesuchenden Person wäre für den Prototyp unverhältnismässig. Gleichzeitig
soll die Nähe helfen, wenn mehrere Angebote fachlich gleich geeignet sind.

## Entscheid

Der Browser fragt den Standort nur nach einem ausdrücklichen Klick ab. Die
Koordinaten werden auf drei Dezimalstellen gerundet, bei jedem relevanten
API-Aufruf optional mitgesendet und weder in der Dialogsession noch in der
Datenbank gespeichert.

Sicherheits-, Zugangs-, Veröffentlichungs- und Aktualitätsregeln bleiben
vorrangig. Erst bei identischem Eignungsscore sortiert die deterministisch
berechnete Luftliniendistanz. Ein fehlender Standort ist kein fachlicher
Ausschlussgrund; bei gleicher Eignung folgen solche Angebote nach Angeboten
mit berechenbarer Distanz. Seit ADR 0010 kann die öffentliche Auswahl dadurch
auf einen tieferen Rang außerhalb der drei angezeigten Treffer fallen.

Angebotsadressen und -koordinaten werden als getrennte verifizierte öffentliche
Katalogdaten geführt. Eine vorhandene Adresse wird auch dann angezeigt, wenn
noch keine Koordinaten hinterlegt sind. Die Distanz wird lokal im
Matching-Service mit der Haversine-Formel berechnet und setzt Koordinaten voraus;
ein externer Routing-Dienst ist nicht erforderlich. Der Wegbeschreibungslink
führt zu Google Maps und verwendet bevorzugt den öffentlichen Zielpunkt, sonst
die öffentliche Adresse des Angebots. Er enthält nie den Ausgangspunkt der
suchenden Person.

Standortkoordinaten und konkrete Distanzen werden weder an das AI-Modell
übermittelt noch im AI- oder Workflow-Audit gespeichert. Das Workflow-Audit
merkt lediglich, ob die optionale Standortfunktion verwendet wurde.

## Konsequenzen

- Ohne Standortfreigabe bleibt die fachliche Rangfolge unverändert.
- Die angezeigte Distanz ist ausdrücklich eine ungefähre Luftlinie und keine
  Gehstrecke oder Zeitangabe.
- Das bestehende PostGIS-Feld und `contact.address` genügen; es ist keine
  zusätzliche Datenbankmigration erforderlich.
- Für grössere Kataloge kann die Distanzberechnung später in eine räumliche
  PostGIS-Abfrage verschoben werden, ohne den öffentlichen API-Vertrag zu
  ändern.
- Manuelle Ortseingabe, Radiusfilter und ein eigener Routing-Dienst sind nicht
  Teil dieses Prototyps.
