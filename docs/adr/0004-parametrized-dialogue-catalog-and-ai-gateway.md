# ADR 0004: Parametrisierte Fachkonfiguration und provider-unabhängiges AI-Gateway

- Status: angenommen
- Datum: 2026-07-26

## Kontext

Punkt 4 der Produktvision sieht vor, dass AI Fragen und Ergebnisinformationen
kontrolliert vereinfachen darf, ohne die Vermittlungsentscheidung zu
übernehmen (ADR 0002). Damit das prüfbar wird, statt nur geplant zu sein,
brauchte es zwei Dinge: einen Fachkonfigurations-Katalog, der Bedarfe,
Merkmale und Fragen aus dem Code in Daten überführt, und eine AI-Anbindung,
die sich unabhängig von einem konkreten Modellanbieter aufrufen, validieren
und abschalten lässt.

Der bisherige Code war vollständig hartcodiert: `Need` (3 Werte) und
`AccessRules` (5 Felder) waren Python-Enums/Dataclasses, gespiegelt in
Request-Schema, JSON-Contract und beiden Repository-Implementierungen. Jedes
neue Merkmal hätte sechs Stellen im Code berührt.

## Entscheid

Zielarchitektur des Dialog-Pfads (umgesetzter Teil in dieser ADR fett):

```text
Mobile PWA
   |
   v
**Dialogue-API** (/v1/dialogue/interpret|start|answer)
   |
   v
**Dialog-Orchestrator**
   +-- Sicherheitsstatus (vor jedem Matching-Aufruf, ADR 0002)
   +-- **Dialogzustand** (in-memory, TTL, proposed/confirmed/unknown/declined)
   +-- **Next-Question-Policy** (datengetrieben aus verbleibenden Kandidaten)
   +-- MatchingService (unveraendert, deterministisch)
          |
          v
**AiGateway** (provider-agnostisch)
   +-- **TemplateGateway** (Default, kein Modellaufruf)
   +-- **AnthropicGateway** / **OpenAiGateway** (optional, hinter Flag + Validatoren)
          |
          v
**Fachkonfigurations-Katalog** (need/attribute/question_definitions)
```

### 1. Katalog wird parametrisiert, Angebotsdaten bleiben JSONB

`need_definitions`, `attribute_definitions`, `attribute_options` und
`question_definitions` (+ Lokalisierungen) sind neue, migrierte Tabellen
(`20260726_0004_dialogue_catalog.py`) mit einem dualen JSON/Postgres-Repository
nach dem bestehenden Muster von `OfferRepository`. `offers.access_rules`
bleibt bewusst unverändert als JSONB — eine volle EAV-Normalisierung der
Angebotsfakten und ein generischer Matching-Regel-DSL sind zurückgestellt.
Begründung: Für 3 Bedarfe und 5 Merkmale ist das Über-Engineering; die
Erweiterung lohnt sich erst bei einer zweiten, nicht-technischen
Fachredaktion oder deutlich mehr Zugangsmerkmalen.

### 2. Dialogzustand bleibt in-memory, nicht in Postgres

`DialogueSessionStore` ist ein kurzlebiger In-Memory-TTL-Store (Standard 45
Minuten). Der technische Prototyp läuft auf einer einzelnen Instanz
(docs/hosting.md); eine `dialogue_sessions`-Tabelle ist ein direkter Ersatz,
sobald horizontal skaliert wird. Freitext wird nach der Interpretation nicht
dauerhaft gespeichert (Datensparsamkeit, docs/architecture.md).

### 3. Drei schmale AI-Schnittstellen statt einem Chat-Prompt

`InterpretationPort`, `QuestionRendererPort`, `ResultExplainerPort` sind
unabhängig testbare Protocols. Der Dialog-Orchestrator entscheidet, *was*
gefragt oder gezeigt werden darf; AI bestimmt nur, *wie* es formuliert wird.
Eine AI-Interpretation kann nie direkt zu einem bestätigten Merkmal werden
(`AttributeState.__post_init__` erzwingt das strukturell).

### 4. AiGateway ist provider-unabhängig — Template zuerst, dann Live

`TemplateGateway` implementiert alle drei Ports ohne Modellaufruf und ist der
produktive Fallback, nicht nur ein Demo-Zustand: Er läuft immer, wenn
`VESTA_AI_ENABLED=false` ist oder ein Live-Aufruf fehlschlägt oder eine
Vertragsregel verletzt (`ai/validators.py` prüft Fakten-Bezug, unveränderte
Antwortoptionen, erlaubte Aktionen und einen Wortfilter gegen
Zusicherungsformulierungen).

`AiGateway` kennt die konkrete Modell-Implementierung nicht — sie wird als
strukturelles `LiveGateway`-Protocol injiziert. Dadurch liessen sich zwei
reale Implementierungen bauen und **live gegen echte Modelle verifizieren**,
ohne `AiGateway`, die Validatoren oder die Routen anzufassen:

- `ai/live_gateway.py` — Anthropic Messages API (`claude-haiku-4-5`,
  `output_config.format` für Schema-constrained JSON)
- `ai/openai_gateway.py` — OpenAI Chat Completions API (`gpt-4o-mini`,
  `response_format: json_schema` mit `strict: true`), auf Nutzerwunsch
  ergänzt und mit einem echten API-Aufruf gegen `ResultExplainerPort`
  verifiziert (bestand alle Validator-Prüfungen)

Beide teilen sich JSON-Schemas, System-Prompts und Hilfsfunktionen; nur der
API-Client unterscheidet sich. `settings.ai_provider` wählt zur Laufzeit.

### 5. Datenübertragung bleibt eine offene Freigabebedingung

`docs/hosting.md` verlangt bereits: "Die AI-Schnittstelle darf nicht
stillschweigend Daten in eine andere Region übertragen. Sie bleibt im MVP
deaktiviert, bis Vertrag, Zweck und Datenfluss freigegeben sind." Das gilt
unverändert für **beide** Provider. `VESTA_AI_ENABLED` ist per Default
`false`; ein Providerwechsel (Anthropic ↔ OpenAI) ändert nichts an dieser
Freigabebedingung — er verdoppelt sie eher, da damit zwei mögliche
Sub-Prozessoren mit unterschiedlichen Datenstandorten zur Debatte stehen.
Vor einem Feldeinsatz muss die in `docs/hosting.md` genannte "separate
Prüfung eines späteren AI-/Sprachmodell-Anbieters" für den tatsächlich
gewählten Anbieter erfolgen.

## Konsequenzen

- Ein neues Zugangsmerkmal lässt sich künftig über den Katalog ergänzen,
  sofern es sich in `boolean | integer | enum` abbilden lässt; ein
  grundsätzlich neuer Merkmalstyp oder eine neue Regel-Operator-Klasse
  bleibt bewusst eine Codeänderung.
- Die Vermittlung bleibt ohne AI vollständig funktions- und testfähig
  (`TemplateGateway`), wie in ADR 0002 gefordert — das wurde nicht nur
  behauptet, sondern per Testfall (`test_ai_gateway.py`) und manuellem
  Fallback-Nachweis gezeigt.
- Ein Providerwechsel bei den Live-Modellen berührt nur `main.py`s
  `create_ai_gateway()` und eine neue `*_gateway.py`-Datei — Ports, Routen,
  Validatoren und Contracts bleiben unverändert.
- Vor einem echten Feldpilot fehlen weiterhin: EAV-Normalisierung der
  Angebotsfakten (falls mehr als eine Organisation Regeln pflegt),
  Postgres-Sessions (bei horizontaler Skalierung), und die formelle
  Datenschutz-/Datenfluss-Freigabe für den gewählten AI-Anbieter.
