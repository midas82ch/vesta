# ADR 0005: AI-Audit-Log und eigener Admin-Zugang

- Status: angenommen
- Datum: 2026-07-27

## Kontext

Bisher war jede AI-Gateway-Interaktion (Freitext-Interpretation,
Fragen-Formulierung, Ergebnis-Erklärung) nur im Erfolgsfall über den
zurückgegebenen `source`-Wert ("ai"/"template") sichtbar; ein Fallback wurde
lediglich als Warnung geloggt (`logger.warning`/`logger.exception`), nicht
persistiert. Es gab keine Möglichkeit nachzuvollziehen, was ein Modell
tatsächlich als Prompt erhalten und geantwortet hat, und keinen Adminbereich,
um das überhaupt anzuzeigen — beides existierte im Projekt noch nicht.

`docs/architecture.md` ("Datenschutz") legt fest: *"Freitext wird im MVP
nicht dauerhaft gespeichert"* und *"Logs enthalten technische IDs, keine
vollständigen Eingaben."* Ein Volltext-Audit der AI-Kommunikation steht dazu
im Widerspruch. Das wurde bewusst in Kauf genommen und ist Gegenstand dieser
ADR, nicht stillschweigend umgangen.

## Entscheid

### 1. Volltext-Audit mit manueller statt automatischer Löschung

Jeder tatsächlich versuchte Live-AI-Aufruf (nicht: Template-Modus, da dort
keine AI-Kommunikation stattfindet) wird in `ai_interaction_log`
gespeichert — inklusive vollem Prompt- und Antwort-Text, Provider/Modell,
Ergebnis (`ai` / `fallback_validation` / `fallback_error`) und ggf.
Validierungs-Verstössen. Die Einträge bleiben gespeichert, bis sie später
manuell entfernt werden. Eine automatische Löschung und eine Löschoberfläche
sind nicht Teil dieses Prototyps. Die frühere Datenschutz-Aussage
"keine vollständigen Eingaben" gilt für diesen einen, klar abgegrenzten Zweck
(Admin-Audit) nicht mehr — der öffentliche Datenschutztext wurde entsprechend
ergänzt.

Aufgezeichnet wird nur, wenn `VESTA_AI_ENABLED=true` ist und tatsächlich ein
Live-Aufruf versucht wurde; im reinen Template-Betrieb entstehen keine
Einträge.

### 2. Eigener, DB-basierter Admin-Login statt Basic-Auth

Es gibt eine neue `admin_users`-Tabelle (Benutzername + Passwort-Hash,
`hashlib.scrypt`) statt eines einzelnen Zugangs über Settings/Secret oder
Basic-Auth am Reverse Proxy. Admins werden ausschliesslich über das
interaktive CLI `vesta_api.cli.create_admin_user` angelegt (gegen die
Admin-DB-Verbindung, gleiches Muster wie `provision_database_roles.py`) —
es gibt bewusst keinen HTTP-Endpunkt zum Anlegen neuer Admins. Sessions sind
ein In-Memory-TTL-Store (`AdminSessionStore`, 8 Stunden), gleiche
Begründung wie bei `DialogueSessionStore`: der Prototyp läuft auf einer
einzelnen Instanz.

Der Adminbereich (`/admin/*` im Web, `/v1/admin/*` in der API) ist bewusst
nicht mehrsprachig — internes Werkzeug, kein Teil des öffentlichen
i18n-Katalogs.

### 3. Rohdaten-Erfassung ohne Änderung der AI-Port-Verträge

`AnthropicGateway`/`OpenAiGateway` bekommen ein zusätzliches, request-lokales
`last_exchange`-Attribut auf Basis von `ContextVar` (Request-/Response-Text),
das `AiGateway` per `getattr(..., "last_exchange", None)` ausliest. Dadurch
werden parallele Sessions nicht vermischt. Die drei Port-Signaturen
(`InterpretationPort`, `QuestionRendererPort`, `ResultExplainerPort`) ändern
sich nicht — Stubs/Tests ohne dieses Attribut funktionieren unverändert.

## Konsequenzen

- Der Adminbereich macht sichtbar, wie oft und warum auf den Template-
  Fallback zurückgefallen wird (Validierungsfehler vs. technischer Fehler),
  was vorher nur in unstrukturierten Logs sichtbar war.
- Die Datenschutzerklärung musste inhaltlich angepasst werden (siehe
  `apps/web/lib/i18n.ts`, `privacy.ai.text`) — das AI-Volltext-Audit ist ein
  neuer Ausnahmefall von der sonst geltenden
  Datensparsamkeits-Regel, nicht deren Aufhebung.
- Das Audit-Log wächst ohne automatische Bereinigung. Eine spätere manuelle
  Löschfunktion und eine dazugehörige Betriebsregel bleiben bewusst offen.
- Ein Wechsel auf mehrere Admin-Rollen/-Rechte (z. B. Nur-Lese vs. Vollzugriff)
  ist über die bestehende `admin_users`-Tabelle möglich, aber nicht Teil
  dieses Umfangs.
- Vor einem echten Feldpilot bleibt offen: ein persistenter, horizontal
  skalierbarer Session-Store (analog zur bereits in ADR 0004 genannten
  Einschränkung bei `DialogueSessionStore`), falls die API je auf mehr als
  eine Instanz skaliert.
