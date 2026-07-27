export const supportedLocales = ["de", "fr", "en", "ar"] as const;

export type Locale = (typeof supportedLocales)[number];

const de = {
  "a11y.skipToContent": "Direkt zum Inhalt",
  "a11y.opensNewTab": "öffnet in einem neuen Tab",
  "brand.homeLabel": "Vesta Startseite",
  "pilot.label": "Pilot · Bern",
  "nav.primaryLabel": "Hauptnavigation",
  "nav.home": "Suche",
  "nav.imprint": "Impressum",
  "nav.privacy": "Datenschutz",
  "locale.label": "Sprache der Oberfläche",
  "locale.de": "Deutsch",
  "locale.fr": "Français",
  "locale.en": "English",
  "locale.ar": "العربية",
  "pwa.install": "App installieren",
  "hero.eyebrow": "Berner Sozial-Lotse",
  "hero.title": "Was brauchst du gerade?",
  "hero.lead":
    "Finde passende soziale Angebote in Bern – einfach und mit sichtbaren Quellen.",
  "hero.trust":
    "Du brauchst kein Konto. Deine Suche wird nicht als Dossier gespeichert.",
  "form.help":
    "Beantworte nur die Angaben, die für deine Suche wichtig sind. Danach werden mögliche Angebote angezeigt.",
  "form.need.legend": "Wähle einen Bereich",
  "need.sleep.title": "Heute schlafen",
  "need.sleep.detail": "Einen Platz für die Nacht suchen",
  "need.basic.title": "Grundversorgung",
  "need.basic.detail": "Essen, Dusche oder Ersthilfe",
  "need.counselling.title": "Beratung",
  "need.counselling.detail": "Hilfe bei Sucht, Wohnen oder Geld",
  "form.targetGroup.label": "Zielgruppe",
  "form.targetGroup.hint":
    "Die Angabe hilft, Angebote mit besonderen Zugangsbedingungen korrekt einzuordnen.",
  "form.targetGroup.none": "Keine Angabe",
  "form.targetGroup.finta": "Frau / FINTA",
  "form.targetGroup.other": "Andere / allgemeine Suche",
  "form.additional.legend": "Weitere Angaben",
  "form.dog": "Ich habe einen Hund",
  "form.noIdentity": "Ich habe keinen Ausweis",
  "form.submit": "Passende Hilfe finden",
  "form.loading": "Angebote werden geprüft …",
  "status.loading": "Die Angebote werden geprüft.",
  "error.search":
    "Die Suche ist gerade nicht erreichbar. Bitte versuche es später erneut oder wende dich direkt an eine Fachperson.",
  "results.eyebrow": "Ergebnis",
  "results.count.zero": "Keine passenden Testangebote",
  "results.count.one": "Ein mögliches Angebot",
  "results.count.two": "{count} mögliche Angebote",
  "results.count.few": "{count} mögliche Angebote",
  "results.count.many": "{count} mögliche Angebote",
  "results.count.other": "{count} mögliche Angebote",
  "results.demoBadge": "Testdaten · nicht für den Feldeinsatz",
  "availability.confirmed": "Status bestätigt",
  "availability.call_to_confirm": "Bitte vorher abklären",
  "availability.unknown": "Status unbekannt",
  "results.uncertainty": "Einzelne Angaben müssen abgeklärt werden.",
  "results.originalLanguage": "Angebotsangaben im Original auf Deutsch",
  "results.checked": "Automatisch geprüft am {date}",
  "results.source": "Quelle",
  "results.distance.meters": "ca. {distance} m Luftlinie",
  "results.distance.kilometers": "ca. {distance} km Luftlinie",
  "results.address": "Adresse",
  "results.directions": "Wegbeschreibung in Google Maps",
  "results.handoff":
    "Wir haben kein verlässlich passendes Angebot gefunden. Eine Fachperson sollte die Situation übernehmen.",
  "results.disclaimer":
    "Angebote werden nicht automatisch reserviert. Aktualität und Kontaktangaben vor Ort bestätigen.",
  "principles.eyebrow": "Wie Vesta arbeitet",
  "principles.title": "Technik, die den Zugang erleichtert.",
  "principle.verified.title": "Geprüfte Information",
  "principle.verified.text":
    "Jedes Ergebnis zeigt Quelle, Prüfdatum und bestehende Unsicherheiten.",
  "principle.rules.title": "Klare Regeln",
  "principle.rules.text":
    "Zugangsbedingungen werden nachvollziehbar geprüft – nicht von AI entschieden.",
  "principle.handoff.title": "Menschliche Übergabe",
  "principle.handoff.text":
    "Bei Gefahr, Unsicherheit oder auf Wunsch übernimmt eine Fachperson.",
  "about.back": "Zur Hilfe-Suche",
  "about.eyebrow": "Über Vesta & Impressum",
  "about.title": "Weniger Systemreibung. Mehr Zugang zu Hilfe.",
  "about.lead":
    "Vesta entwickelt eine verifizierte, mehrsprachige Zugangsschicht für das Berner Hilfesystem. Bestehende Hilfe soll leichter auffindbar, verständlich und überprüfbar werden.",
  "about.problem.eyebrow": "Warum Vesta",
  "about.problem.title":
    "Hilfe ist vorhanden. Der Weg dorthin ist oft kompliziert.",
  "about.problem.text":
    "Angebote, Zuständigkeiten und Zugangsbedingungen sind über viele Stellen verteilt. Vesta setzt dort an, wo digitale Unterstützung realistisch helfen kann: bei Orientierung, Sprache und einem verständlichen nächsten Schritt.",
  "about.people.title": "Für Menschen",
  "about.people.text":
    "Weniger Fachsprache, weniger Umwege und passende Angebote mit sichtbaren Quellen und Unsicherheiten.",
  "about.professionals.title": "Für Fachpersonen",
  "about.professionals.text":
    "Weniger wiederkehrende Recherche und eine verlässliche gemeinsame Wissensbasis für die Vermittlung.",
  "about.system.title": "Für Bern",
  "about.system.text":
    "Erfolglose Hilfewege und fehlende Angebote können sichtbar werden, ohne daraus Personenprofile zu erstellen.",
  "about.responsibility.eyebrow": "Verantwortung",
  "about.responsibility.title":
    "AI erklärt. Regeln prüfen. Menschen übernehmen.",
  "about.responsibility.text":
    "Vesta automatisiert keine Fallentscheide und verteilt keine knappen Plätze. AI darf Sprache verstehen und geprüfte Informationen erklären. Sicherheit, Zugang und Übergaben bleiben nachvollziehbaren Regeln und verantwortlichen Menschen vorbehalten.",
  "about.pilot.eyebrow": "Pilotprojekt",
  "about.pilot.title": "Klein starten. Gemeinsam lernen.",
  "about.pilot.text":
    "Der erste Prototyp konzentriert sich auf Übernachtung, Grundversorgung und Beratung. Er arbeitet ohne Konto und ohne Personendossier. Betroffene, Fachpersonen und Organisationen sollen mitbestimmen, was nützlich und sicher ist.",
  "about.pilot.link": "Projekt auf GitHub ansehen",
  "about.pilot.note":
    "Der technische Prototyp ist öffentlich einsehbar. Rückmeldungen und Mitwirkung sind willkommen.",
  "imprint.eyebrow": "Transparenz",
  "imprint.title": "Impressum",
  "imprint.project.label": "Projekt",
  "imprint.project.value": "Vesta – Berner Sozial-Lotse",
  "imprint.status.label": "Status",
  "imprint.status.value": "Unabhängiger technischer Prototyp in Entwicklung",
  "imprint.responsibility.label": "Trägerschaft",
  "imprint.responsibility.value":
    "Für einen öffentlichen Feldbetrieb noch nicht formell bestimmt",
  "imprint.contact.label": "Projekt und Rückmeldungen",
  "imprint.contact.value": "GitHub-Repository von Vesta",
  "imprint.note":
    "Vor einem öffentlichen Feldbetrieb werden verantwortliche Kontaktstelle, Trägerschaft, Datenschutzinformationen und beteiligte Partner verbindlich ergänzt.",
  "privacy.eyebrow": "Transparenz",
  "privacy.title": "Datenschutzerklärung",
  "privacy.lead":
    "Vesta befindet sich in einer frühen Pilotphase. Diese Seite beschreibt, welche Daten wir aktuell verarbeiten – bewusst so wenig wie möglich.",
  "privacy.scope.eyebrow": "Was wir verarbeiten",
  "privacy.scope.title": "Nur die Angaben deiner aktuellen Suche",
  "privacy.scope.text":
    "Für eine Suche verarbeitet Vesta ausschliesslich die Angaben, die du im Formular auswählst: den gewählten Bereich, deine Sprache und optionale Angaben wie Hund, fehlender Ausweis, Zielgruppe, Alter oder Sicherheitshinweise. Diese Angaben werden nur für die einzelne Suche verwendet.",
  "privacy.scope.noAccount":
    "Vesta funktioniert ohne Konto. Deine Suche wird nicht als Dossier oder Profil gespeichert.",
  "privacy.location.eyebrow": "Optionaler Standort",
  "privacy.location.title": "Nur nach deiner ausdrücklichen Freigabe",
  "privacy.location.text":
    "Wenn du «Standort verwenden» auswählst, rundet Vesta die Browserposition auf ungefähr 100 Meter und verwendet sie nur zur Berechnung der Luftlinie und zur Sortierung gleich geeigneter Angebote. Die Position und die berechneten Distanzen werden weder gespeichert noch an das AI-Modell übermittelt. Der externe Google-Maps-Link enthält nur das öffentliche Ziel des Angebots, nicht deinen Ausgangspunkt.",
  "privacy.storage.eyebrow": "Speicherung",
  "privacy.storage.title": "Keine dauerhafte Speicherung deiner Suche",
  "privacy.storage.text":
    "Die Angaben deiner Suche werden an die Vesta-API übermittelt, dort für die Auswertung verwendet und danach nicht in einer Datenbank gespeichert. Es entsteht kein Verlauf früherer Suchen.",
  "privacy.device.eyebrow": "Auf deinem Gerät",
  "privacy.device.title": "Nur deine Spracheinstellung",
  "privacy.device.text":
    "Vesta speichert lokal auf deinem Gerät ausschliesslich deine gewählte Sprache, damit die Oberfläche beim nächsten Besuch in der richtigen Sprache erscheint. Diese Angabe verlässt dein Gerät nicht.",
  "privacy.offline.eyebrow": "Offline-Nutzung",
  "privacy.offline.title": "Der Offline-Speicher enthält keine Suchergebnisse",
  "privacy.offline.text":
    "Für die Installation als App speichert Vesta technische Bestandteile wie Seitengerüst, Symbole und Schriften zwischen. Anfragen an die Such-API werden davon ausdrücklich ausgenommen und nie zwischengespeichert.",
  "privacy.logs.eyebrow": "Technische Protokolle",
  "privacy.logs.title": "Betriebs-Logs enthalten keine vollständigen Eingaben",
  "privacy.logs.text":
    "Der Betrieb der Website erzeugt wie bei jedem Webdienst technische Protokolle, zum Beispiel IP-Adresse, Zeitpunkt und aufgerufene Adresse, für Sicherheit und Fehlersuche. Aufbewahrungsdauer und Löschprozess sind vor einem öffentlichen Feldbetrieb verbindlich festzulegen.",
  "privacy.offers.eyebrow": "Angebotsregister",
  "privacy.offers.title": "Öffentliche Informationen zu Hilfsangeboten",
  "privacy.offers.text":
    "Das Angebotsregister enthält geprüfte, öffentliche Informationen zu Hilfsangeboten in Bern – keine personenbezogenen Daten von Nutzenden.",
  "privacy.ai.eyebrow": "AI",
  "privacy.ai.title": "AI-Sprachmodell im Testbetrieb",
  "privacy.ai.text":
    "Freitexte, freigegebene Fragen und begrenzte Angebotsfakten werden zur Interpretation und verständlichen Formulierung an OpenAI übermittelt. Die AI entscheidet weder über den Zugang noch über Plätze. Bitte keine Namen, Adressen oder Kontaktdaten eingeben. Eingaben, AI-Anfragen und -Antworten, die dazwischenliegende Vesta-Systemlogik und die ausgegebene Antwort werden als zusammenhängender Workflow bis zur manuellen Löschung gespeichert und sind nur für berechtigte Administratorinnen und Administratoren einsehbar.",
  "privacy.hosting.eyebrow": "Hosting",
  "privacy.hosting.title": "Schweizer Infrastruktur vorgesehen",
  "privacy.hosting.text":
    "Für den Betrieb ist Infrastruktur in der Schweiz vorgesehen. Vor einem öffentlichen Feldbetrieb werden Auftragsbearbeitungsvertrag, Subprozessoren, Speicherorte und eine Datenschutz-Folgenabschätzung verbindlich geklärt.",
  "privacy.rights.eyebrow": "Deine Rechte",
  "privacy.rights.title": "Auskunft, Berichtigung und Löschung",
  "privacy.rights.text":
    "Da Vesta ohne Konto arbeitet und keine Suchverläufe speichert, betreffen Auskunfts-, Berichtigungs- und Löschungsrechte vor allem technische Protokolle. Bitte wende dich dafür an die unten genannte Kontaktstelle.",
  "privacy.responsible.eyebrow": "Verantwortliche Stelle",
  "privacy.responsible.title": "Noch nicht formell bestimmt",
  "privacy.responsible.text":
    "Vesta ist aktuell ein unabhängiger technischer Prototyp. Eine verantwortliche Stelle für den öffentlichen Feldbetrieb ist noch nicht formell bestimmt.",
  "privacy.contact.label": "Fragen und Rückmeldungen",
  "privacy.contact.value": "GitHub-Repository von Vesta",
  "privacy.note":
    "Diese Erklärung beschreibt den aktuellen Prototyp-Stand. Vor einem öffentlichen Feldbetrieb wird sie mit verantwortlicher Kontaktstelle, Trägerschaft und geprüften Subprozessoren verbindlich ergänzt.",
  "footer.emergency": "Vesta ersetzt keine Notfallhilfe und reserviert keine Plätze.",
  "footer.prototype":
    "Initialer Prototyp · Angaben noch nicht für den Feldeinsatz freigegeben",
  "footer.imprint": "Über Vesta & Impressum",
  "footer.privacy": "Datenschutzerklärung",
  "offline.eyebrow": "Keine Verbindung",
  "offline.title": "Vesta ist gerade offline.",
  "offline.body":
    "Ohne Internetverbindung zeigen wir bewusst keine möglicherweise veralteten Angebote. Stelle die Verbindung wieder her und versuche es erneut.",
  "offline.retry": "Erneut versuchen",
  "offline.back": "Zur Startseite",
  "dialogue.freeText.label": "Beschreibe kurz, was du brauchst",
  "dialogue.freeText.placeholder":
    "z. B. Ich brauche heute einen Schlafplatz mit meinem Hund",
  "dialogue.freeText.submit": "Vorschlag prüfen",
  "dialogue.freeText.loading": "Wird geprüft …",
  "dialogue.interpretation.unclear":
    "Ich konnte dein Anliegen noch keinem Bereich eindeutig zuordnen. Wähle unten den passenden Bereich.",
  "dialogue.interpretation.needApplied": "Erkannter Bereich: {need}",
  "dialogue.interpretation.confirmLegend": "Passt dieser Bereich?",
  "dialogue.needPicker.legend": "Wähle einen Bereich",
  "dialogue.location.title": "Angebote in deiner Nähe",
  "dialogue.location.text":
    "Optional: Nutze deinen ungefähren Standort, um gleich geeignete Angebote nach Nähe zu sortieren.",
  "dialogue.location.use": "Standort verwenden",
  "dialogue.location.locating": "Standort wird bestimmt …",
  "dialogue.location.active": "Der ungefähre Standort wird für diese Suche verwendet.",
  "dialogue.location.remove": "Standort nicht mehr verwenden",
  "dialogue.location.denied":
    "Der Standort wurde nicht freigegeben. Du kannst ohne Standort fortfahren.",
  "dialogue.location.timeout":
    "Der Standort konnte nicht rechtzeitig bestimmt werden. Du kannst ohne Standort fortfahren.",
  "dialogue.location.unavailable":
    "Die Standortbestimmung ist in diesem Browser nicht verfügbar. Du kannst ohne Standort fortfahren.",
  "dialogue.start": "AI-Dialog starten",
  "dialogue.loading": "Wird verarbeitet …",
  "dialogue.progress.label": "Fortschritt im Hilfe-Dialog",
  "dialogue.progress.need": "Anliegen",
  "dialogue.progress.questions": "Rückfragen",
  "dialogue.progress.results": "Angebote",
  "dialogue.progress.current": "aktuell",
  "dialogue.progress.complete": "abgeschlossen",
  "dialogue.conversation.label": "Dialogverlauf",
  "dialogue.conversation.you": "Du",
  "dialogue.conversation.vesta": "Vesta",
  "dialogue.conversation.selectedNeed": "Gewählt: {need}",
  "dialogue.conversation.interpreted":
    "Ich verstehe dein Anliegen als «{need}». Passt das?",
  "dialogue.conversation.answer": "Deine Antwort: {answer}",
  "dialogue.conversation.resultsReady": "Die passenden Angebote sind bereit.",
  "dialogue.busy.interpreting.title": "Vesta versteht dein Anliegen",
  "dialogue.busy.interpreting.text":
    "Deine Eingabe wird eingeordnet. Das dauert meist nur einen Moment.",
  "dialogue.busy.starting.title": "Vesta bereitet die nächste Frage vor",
  "dialogue.busy.starting.text":
    "Die Systemlogik prüft, welche Angabe für eine sichere Suche noch wichtig ist.",
  "dialogue.busy.answer.title": "Vesta prüft deine Antwort",
  "dialogue.busy.answer.text":
    "Wir bestimmen den nächsten passenden Schritt und prüfen danach mögliche Angebote.",
  "dialogue.error.title": "Das hat nicht geklappt",
  "dialogue.error": "Der AI-Dialog ist gerade nicht erreichbar.",
  "dialogue.question.eyebrow": "Eine Frage noch",
  "dialogue.question.answerLegend": "Deine Antwort",
  "dialogue.question.yes": "Ja",
  "dialogue.question.no": "Nein",
  "dialogue.question.numberLabel": "Ihre Antwort",
  "dialogue.question.numberSubmit": "Bestätigen",
  "dialogue.fit.gender.question":
    "Kommt für dich ein Angebot speziell für Frauen und FINTA-Personen infrage?",
  "dialogue.fit.gender.help":
    "Einige Unterkünfte sind ausschließlich für Frauen und FINTA-Personen zugänglich.",
  "dialogue.fit.gender.yes": "Ja, das passt für mich",
  "dialogue.fit.gender.no":
    "Nein, ich suche ein allgemein zugängliches Angebot",
  "dialogue.fit.age.question": "Geht es um eine volljährige Person?",
  "dialogue.fit.age.help":
    "Einige Schlafangebote sind erst ab 18 Jahren zugänglich.",
  "dialogue.fit.age.adult": "Ja, 18 Jahre oder älter",
  "dialogue.fit.age.minor": "Nein, unter 18 Jahre",
  "dialogue.fit.decline": "Möchte ich nicht angeben",
  "dialogue.result.eyebrow": "Erklärtes Ergebnis",
  "dialogue.result.title": "Das könnte dir weiterhelfen",
  "dialogue.restart": "Neu starten",
  "dialogue.other.title": "Etwas anderes",
  "dialogue.other.detail": "Beschreibe es mit eigenen Worten",
  "dialogue.back": "Zurück",
  "dialogue.interpretation.confirmHint": "Antippen, um fortzufahren",
} as const;

export type MessageKey = keyof typeof de;

const fr: Record<MessageKey, string> = {
  "a11y.skipToContent": "Aller directement au contenu",
  "a11y.opensNewTab": "s’ouvre dans un nouvel onglet",
  "brand.homeLabel": "Page d’accueil de Vesta",
  "pilot.label": "Projet pilote · Berne",
  "nav.primaryLabel": "Navigation principale",
  "nav.home": "Recherche",
  "nav.imprint": "Mentions légales",
  "nav.privacy": "Protection des données",
  "locale.label": "Langue de l’interface",
  "locale.de": "Deutsch",
  "locale.fr": "Français",
  "locale.en": "English",
  "locale.ar": "العربية",
  "pwa.install": "Installer l’application",
  "hero.eyebrow": "Guide social bernois",
  "hero.title": "De quoi as-tu besoin maintenant ?",
  "hero.lead":
    "Trouve des offres sociales adaptées à Berne, simplement et avec des sources visibles.",
  "hero.trust":
    "Aucun compte n’est nécessaire. Ta recherche n’est pas enregistrée comme dossier.",
  "form.help":
    "Indique uniquement ce qui est utile à ta recherche. Les offres possibles seront ensuite affichées.",
  "form.need.legend": "Choisis un domaine",
  "need.sleep.title": "Dormir ce soir",
  "need.sleep.detail": "Chercher une place pour la nuit",
  "need.basic.title": "Besoins essentiels",
  "need.basic.detail": "Repas, douche ou premiers soins",
  "need.counselling.title": "Conseil",
  "need.counselling.detail": "Aide pour la dépendance, le logement ou l’argent",
  "form.targetGroup.label": "Groupe cible",
  "form.targetGroup.hint":
    "Cette indication aide à classer correctement les offres avec des conditions d’accès particulières.",
  "form.targetGroup.none": "Aucune indication",
  "form.targetGroup.finta": "Femme / FINTA",
  "form.targetGroup.other": "Autre / recherche générale",
  "form.additional.legend": "Informations supplémentaires",
  "form.dog": "J’ai un chien",
  "form.noIdentity": "Je n’ai pas de pièce d’identité",
  "form.submit": "Trouver une aide adaptée",
  "form.loading": "Vérification des offres…",
  "status.loading": "Les offres sont en cours de vérification.",
  "error.search":
    "La recherche est momentanément indisponible. Réessaie plus tard ou adresse-toi directement à une personne spécialisée.",
  "results.eyebrow": "Résultat",
  "results.count.zero": "Aucune offre test correspondante",
  "results.count.one": "Une offre possible",
  "results.count.two": "{count} offres possibles",
  "results.count.few": "{count} offres possibles",
  "results.count.many": "{count} offres possibles",
  "results.count.other": "{count} offres possibles",
  "results.demoBadge": "Données test · non destinées au terrain",
  "availability.confirmed": "Statut confirmé",
  "availability.call_to_confirm": "Vérifier au préalable",
  "availability.unknown": "Statut inconnu",
  "results.uncertainty": "Certaines informations doivent être vérifiées.",
  "results.originalLanguage": "Informations originales de l’offre en allemand",
  "results.checked": "Vérification automatique le {date}",
  "results.source": "Source",
  "results.distance.meters": "env. {distance} m à vol d’oiseau",
  "results.distance.kilometers": "env. {distance} km à vol d’oiseau",
  "results.address": "Adresse",
  "results.directions": "Itinéraire dans Google Maps",
  "results.handoff":
    "Nous n’avons pas trouvé d’offre suffisamment fiable. Une personne spécialisée devrait reprendre la situation.",
  "results.disclaimer":
    "Les offres ne sont pas réservées automatiquement. Confirmer sur place leur actualité et les coordonnées.",
  "principles.eyebrow": "Comment fonctionne Vesta",
  "principles.title": "Une technologie qui facilite l’accès.",
  "principle.verified.title": "Informations vérifiées",
  "principle.verified.text":
    "Chaque résultat indique sa source, la date de vérification et les incertitudes.",
  "principle.rules.title": "Règles claires",
  "principle.rules.text":
    "Les conditions d’accès sont vérifiées de manière compréhensible, sans décision de l’IA.",
  "principle.handoff.title": "Relais humain",
  "principle.handoff.text":
    "En cas de danger, d’incertitude ou sur demande, une personne spécialisée prend le relais.",
  "about.back": "Retour à la recherche d’aide",
  "about.eyebrow": "À propos de Vesta & mentions légales",
  "about.title": "Moins de frictions. Un meilleur accès à l’aide.",
  "about.lead":
    "Vesta développe une couche d’accès vérifiée et multilingue pour le système d’aide bernois. Les services existants doivent devenir plus faciles à trouver, à comprendre et à vérifier.",
  "about.problem.eyebrow": "Pourquoi Vesta",
  "about.problem.title":
    "L’aide existe. Le chemin pour y accéder est souvent compliqué.",
  "about.problem.text":
    "Les offres, les responsabilités et les conditions d’accès sont réparties entre de nombreux services. Vesta intervient là où le numérique peut réellement aider : l’orientation, la langue et la prochaine étape à suivre.",
  "about.people.title": "Pour les personnes",
  "about.people.text":
    "Moins de jargon, moins de détours et des offres adaptées avec des sources et des incertitudes visibles.",
  "about.professionals.title": "Pour les spécialistes",
  "about.professionals.text":
    "Moins de recherches répétitives et une base de connaissances commune et fiable pour l’orientation.",
  "about.system.title": "Pour Berne",
  "about.system.text":
    "Les parcours d’aide infructueux et les offres manquantes peuvent devenir visibles sans créer de profils individuels.",
  "about.responsibility.eyebrow": "Responsabilité",
  "about.responsibility.title":
    "L’IA explique. Les règles vérifient. Les humains prennent le relais.",
  "about.responsibility.text":
    "Vesta n’automatise pas les décisions de suivi et n’attribue pas les places limitées. L’IA peut comprendre la langue et expliquer des informations vérifiées. La sécurité, l’accès et les relais restent soumis à des règles transparentes et à la responsabilité humaine.",
  "about.pilot.eyebrow": "Projet pilote",
  "about.pilot.title": "Commencer petit. Apprendre ensemble.",
  "about.pilot.text":
    "Le premier prototype se concentre sur l’hébergement, les besoins essentiels et le conseil. Il fonctionne sans compte ni dossier personnel. Les personnes concernées, les spécialistes et les organisations doivent participer aux décisions sur son utilité et sa sécurité.",
  "about.pilot.link": "Voir le projet sur GitHub",
  "about.pilot.note":
    "Le prototype technique est consultable publiquement. Les retours et la participation sont les bienvenus.",
  "imprint.eyebrow": "Transparence",
  "imprint.title": "Mentions légales",
  "imprint.project.label": "Projet",
  "imprint.project.value": "Vesta – guide social bernois",
  "imprint.status.label": "Statut",
  "imprint.status.value": "Prototype technique indépendant en développement",
  "imprint.responsibility.label": "Organisme responsable",
  "imprint.responsibility.value":
    "Pas encore formellement désigné pour une utilisation publique",
  "imprint.contact.label": "Projet et retours",
  "imprint.contact.value": "Dépôt GitHub de Vesta",
  "imprint.note":
    "Avant toute utilisation publique, le contact responsable, l’organisme porteur, les informations sur la protection des données et les partenaires seront indiqués de manière contraignante.",
  "privacy.eyebrow": "Transparence",
  "privacy.title": "Déclaration de protection des données",
  "privacy.lead":
    "Vesta est encore en phase pilote. Cette page décrit les données que nous traitons actuellement – volontairement le moins possible.",
  "privacy.scope.eyebrow": "Ce que nous traitons",
  "privacy.scope.title": "Uniquement les informations de ta recherche actuelle",
  "privacy.scope.text":
    "Pour une recherche, Vesta traite uniquement les informations que tu sélectionnes dans le formulaire : le domaine choisi, ta langue et des informations optionnelles comme un chien, l’absence de pièce d’identité, le groupe cible, l’âge ou des indications de sécurité. Ces informations ne servent qu’à cette recherche précise.",
  "privacy.scope.noAccount":
    "Vesta fonctionne sans compte. Ta recherche n’est pas enregistrée comme dossier ou profil.",
  "privacy.location.eyebrow": "Localisation facultative",
  "privacy.location.title": "Uniquement avec ton accord explicite",
  "privacy.location.text":
    "Si tu sélectionnes « Utiliser ma position », Vesta arrondit la position du navigateur à environ 100 mètres et l’utilise uniquement pour calculer la distance à vol d’oiseau et trier les offres de même pertinence. La position et les distances calculées ne sont ni enregistrées ni transmises au modèle d’IA. Le lien externe Google Maps contient uniquement la destination publique de l’offre, pas ton point de départ.",
  "privacy.storage.eyebrow": "Conservation",
  "privacy.storage.title": "Aucune conservation durable de ta recherche",
  "privacy.storage.text":
    "Les informations de ta recherche sont transmises à l’API de Vesta, utilisées pour l’évaluation, puis ne sont pas enregistrées dans une base de données. Aucun historique de recherches précédentes n’est créé.",
  "privacy.device.eyebrow": "Sur ton appareil",
  "privacy.device.title": "Uniquement ta préférence de langue",
  "privacy.device.text":
    "Vesta enregistre localement sur ton appareil uniquement la langue choisie, afin que l’interface s’affiche dans la bonne langue lors de ta prochaine visite. Cette information ne quitte jamais ton appareil.",
  "privacy.offline.eyebrow": "Utilisation hors ligne",
  "privacy.offline.title": "Le stockage hors ligne ne contient aucun résultat de recherche",
  "privacy.offline.text":
    "Pour l’installation en tant qu’application, Vesta met en cache des éléments techniques comme la structure des pages, les icônes et les polices. Les requêtes envoyées à l’API de recherche en sont explicitement exclues et ne sont jamais mises en cache.",
  "privacy.logs.eyebrow": "Journaux techniques",
  "privacy.logs.title": "Les journaux d’exploitation ne contiennent pas tes réponses complètes",
  "privacy.logs.text":
    "Comme tout service web, l’exploitation du site génère des journaux techniques, par exemple l’adresse IP, l’heure et l’adresse consultée, à des fins de sécurité et de dépannage. La durée de conservation et le processus de suppression seront définis de manière contraignante avant toute utilisation publique sur le terrain.",
  "privacy.offers.eyebrow": "Registre des offres",
  "privacy.offers.title": "Informations publiques sur les offres d’aide",
  "privacy.offers.text":
    "Le registre des offres contient des informations publiques et vérifiées sur les offres d’aide à Berne – aucune donnée personnelle des utilisateurs et utilisatrices.",
  "privacy.ai.eyebrow": "IA",
  "privacy.ai.title": "Modèle d’IA en phase de test",
  "privacy.ai.text":
    "Les textes libres, les questions validées et des informations limitées sur les offres sont transmis à OpenAI pour interprétation et reformulation. L’IA ne décide ni de l’accès ni de l’attribution de places. Ne saisis aucun nom, adresse ou coordonnée. Les saisies, les requêtes et réponses de l’IA, la logique système intermédiaire de Vesta et la réponse affichée sont conservées sous forme d’un workflow cohérent jusqu’à leur suppression manuelle et ne sont consultables que par les administratrices et administrateurs autorisés.",
  "privacy.hosting.eyebrow": "Hébergement",
  "privacy.hosting.title": "Infrastructure suisse prévue",
  "privacy.hosting.text":
    "L’exploitation est prévue sur une infrastructure suisse. Avant toute utilisation publique sur le terrain, le contrat de sous-traitance, les sous-traitants, les lieux de stockage et une analyse d’impact relative à la protection des données seront définis de manière contraignante.",
  "privacy.rights.eyebrow": "Tes droits",
  "privacy.rights.title": "Accès, rectification et suppression",
  "privacy.rights.text":
    "Comme Vesta fonctionne sans compte et ne conserve aucun historique de recherche, les droits d’accès, de rectification et de suppression concernent surtout les journaux techniques. Adresse-toi pour cela au contact indiqué ci-dessous.",
  "privacy.responsible.eyebrow": "Organisme responsable",
  "privacy.responsible.title": "Pas encore formellement désigné",
  "privacy.responsible.text":
    "Vesta est actuellement un prototype technique indépendant. Un organisme responsable pour une utilisation publique sur le terrain n’a pas encore été formellement désigné.",
  "privacy.contact.label": "Questions et retours",
  "privacy.contact.value": "Dépôt GitHub de Vesta",
  "privacy.note":
    "Cette déclaration décrit l’état actuel du prototype. Avant toute utilisation publique sur le terrain, elle sera complétée de manière contraignante avec un contact responsable, un organisme porteur et des sous-traitants vérifiés.",
  "footer.emergency":
    "Vesta ne remplace pas l’aide d’urgence et ne réserve aucune place.",
  "footer.prototype":
    "Prototype initial · informations non encore autorisées pour le terrain",
  "footer.imprint": "À propos & mentions légales",
  "footer.privacy": "Déclaration de protection des données",
  "offline.eyebrow": "Pas de connexion",
  "offline.title": "Vesta est actuellement hors ligne.",
  "offline.body":
    "Sans connexion internet, nous n’affichons volontairement aucune offre potentiellement obsolète. Rétablis la connexion et réessaie.",
  "offline.retry": "Réessayer",
  "offline.back": "Retour à l’accueil",
  "dialogue.freeText.label": "Décris brièvement ce dont tu as besoin",
  "dialogue.freeText.placeholder":
    "p. ex. J'ai besoin d'une place pour dormir ce soir avec mon chien",
  "dialogue.freeText.submit": "Vérifier la proposition",
  "dialogue.freeText.loading": "Vérification en cours …",
  "dialogue.interpretation.unclear":
    "Je n’ai pas encore pu attribuer clairement ta demande à un domaine. Choisis ci-dessous le domaine qui convient.",
  "dialogue.interpretation.needApplied": "Domaine reconnu : {need}",
  "dialogue.interpretation.confirmLegend": "Ce domaine correspond-il ?",
  "dialogue.needPicker.legend": "Choisis un domaine",
  "dialogue.location.title": "Offres près de toi",
  "dialogue.location.text":
    "Facultatif : utilise ta position approximative pour trier par proximité les offres de même pertinence.",
  "dialogue.location.use": "Utiliser ma position",
  "dialogue.location.locating": "Localisation en cours…",
  "dialogue.location.active":
    "La position approximative est utilisée pour cette recherche.",
  "dialogue.location.remove": "Ne plus utiliser ma position",
  "dialogue.location.denied":
    "La position n’a pas été autorisée. Tu peux continuer sans localisation.",
  "dialogue.location.timeout":
    "La position n’a pas pu être déterminée à temps. Tu peux continuer sans localisation.",
  "dialogue.location.unavailable":
    "La localisation n’est pas disponible dans ce navigateur. Tu peux continuer sans localisation.",
  "dialogue.start": "Démarrer le dialogue AI",
  "dialogue.loading": "Traitement en cours …",
  "dialogue.progress.label": "Progression dans le dialogue d’aide",
  "dialogue.progress.need": "Demande",
  "dialogue.progress.questions": "Questions",
  "dialogue.progress.results": "Offres",
  "dialogue.progress.current": "étape actuelle",
  "dialogue.progress.complete": "terminé",
  "dialogue.conversation.label": "Déroulement du dialogue",
  "dialogue.conversation.you": "Toi",
  "dialogue.conversation.vesta": "Vesta",
  "dialogue.conversation.selectedNeed": "Choix : {need}",
  "dialogue.conversation.interpreted":
    "Je comprends ta demande comme « {need} ». Est-ce correct ?",
  "dialogue.conversation.answer": "Ta réponse : {answer}",
  "dialogue.conversation.resultsReady": "Les offres adaptées sont prêtes.",
  "dialogue.busy.interpreting.title": "Vesta comprend ta demande",
  "dialogue.busy.interpreting.text":
    "Ta saisie est en cours de classement. Cela ne prend généralement qu’un instant.",
  "dialogue.busy.starting.title": "Vesta prépare la prochaine question",
  "dialogue.busy.starting.text":
    "La logique du système vérifie quelle information est encore importante pour une recherche sûre.",
  "dialogue.busy.answer.title": "Vesta vérifie ta réponse",
  "dialogue.busy.answer.text":
    "Nous déterminons la prochaine étape appropriée, puis vérifions les offres possibles.",
  "dialogue.error.title": "Une erreur s’est produite",
  "dialogue.error": "Le dialogue AI n'est pas disponible actuellement.",
  "dialogue.question.eyebrow": "Encore une question",
  "dialogue.question.answerLegend": "Ta réponse",
  "dialogue.question.yes": "Oui",
  "dialogue.question.no": "Non",
  "dialogue.question.numberLabel": "Votre réponse",
  "dialogue.question.numberSubmit": "Confirmer",
  "dialogue.fit.gender.question":
    "Une offre spécialement destinée aux femmes et aux personnes FINTA te convient-elle ?",
  "dialogue.fit.gender.help":
    "Certains hébergements sont exclusivement accessibles aux femmes et aux personnes FINTA.",
  "dialogue.fit.gender.yes": "Oui, cela me convient",
  "dialogue.fit.gender.no": "Non, je cherche une offre accessible à tous",
  "dialogue.fit.age.question":
    "La recherche concerne-t-elle une personne majeure ?",
  "dialogue.fit.age.help":
    "Certains hébergements ne sont accessibles qu’à partir de 18 ans.",
  "dialogue.fit.age.adult": "Oui, 18 ans ou plus",
  "dialogue.fit.age.minor": "Non, moins de 18 ans",
  "dialogue.fit.decline": "Je préfère ne pas l’indiquer",
  "dialogue.result.eyebrow": "Résultat expliqué",
  "dialogue.result.title": "Voici ce qui pourrait t’aider",
  "dialogue.restart": "Recommencer",
  "dialogue.other.title": "Autre chose",
  "dialogue.other.detail": "Décris-le avec tes propres mots",
  "dialogue.back": "Retour",
  "dialogue.interpretation.confirmHint": "Toucher pour continuer",
};

const en: Record<MessageKey, string> = {
  "a11y.skipToContent": "Skip to content",
  "a11y.opensNewTab": "opens in a new tab",
  "brand.homeLabel": "Vesta home page",
  "pilot.label": "Pilot · Bern",
  "nav.primaryLabel": "Main navigation",
  "nav.home": "Search",
  "nav.imprint": "Imprint",
  "nav.privacy": "Privacy",
  "locale.label": "Interface language",
  "locale.de": "Deutsch",
  "locale.fr": "Français",
  "locale.en": "English",
  "locale.ar": "العربية",
  "pwa.install": "Install app",
  "hero.eyebrow": "Bern social services guide",
  "hero.title": "What do you need right now?",
  "hero.lead":
    "Find suitable social services in Bern, simply and with visible sources.",
  "hero.trust":
    "You do not need an account. Your search is not stored as a case file.",
  "form.help":
    "Only provide details that matter to your search. Possible services will then be shown.",
  "form.need.legend": "Choose an area",
  "need.sleep.title": "A place to sleep tonight",
  "need.sleep.detail": "Find somewhere to stay for the night",
  "need.basic.title": "Basic needs",
  "need.basic.detail": "Food, a shower or first aid",
  "need.counselling.title": "Advice",
  "need.counselling.detail": "Help with addiction, housing or money",
  "form.targetGroup.label": "Target group",
  "form.targetGroup.hint":
    "This helps classify services with specific access conditions correctly.",
  "form.targetGroup.none": "Prefer not to say",
  "form.targetGroup.finta": "Woman / FINTA",
  "form.targetGroup.other": "Other / general search",
  "form.additional.legend": "Additional details",
  "form.dog": "I have a dog",
  "form.noIdentity": "I do not have an identity document",
  "form.submit": "Find suitable help",
  "form.loading": "Checking services…",
  "status.loading": "The services are being checked.",
  "error.search":
    "Search is currently unavailable. Please try again later or contact a qualified professional directly.",
  "results.eyebrow": "Result",
  "results.count.zero": "No matching test services",
  "results.count.one": "One possible service",
  "results.count.two": "{count} possible services",
  "results.count.few": "{count} possible services",
  "results.count.many": "{count} possible services",
  "results.count.other": "{count} possible services",
  "results.demoBadge": "Test data · not for field use",
  "availability.confirmed": "Status confirmed",
  "availability.call_to_confirm": "Please check first",
  "availability.unknown": "Status unknown",
  "results.uncertainty": "Some details need to be checked.",
  "results.originalLanguage": "Original service information in German",
  "results.checked": "Automatically checked on {date}",
  "results.source": "Source",
  "results.distance.meters": "approx. {distance} m straight-line distance",
  "results.distance.kilometers": "approx. {distance} km straight-line distance",
  "results.address": "Address",
  "results.directions": "Directions in Google Maps",
  "results.handoff":
    "We could not find a reliably suitable service. A qualified professional should take over.",
  "results.disclaimer":
    "Services are not reserved automatically. Confirm current details and contact information directly.",
  "principles.eyebrow": "How Vesta works",
  "principles.title": "Technology that makes access easier.",
  "principle.verified.title": "Verified information",
  "principle.verified.text":
    "Every result shows its source, verification date and remaining uncertainties.",
  "principle.rules.title": "Clear rules",
  "principle.rules.text":
    "Access conditions are checked transparently and are not decided by AI.",
  "principle.handoff.title": "Human handoff",
  "principle.handoff.text":
    "In case of danger, uncertainty or on request, a qualified professional takes over.",
  "about.back": "Back to help search",
  "about.eyebrow": "About Vesta & legal notice",
  "about.title": "Less system friction. Better access to help.",
  "about.lead":
    "Vesta is developing a verified, multilingual access layer for Bern’s support system. Existing help should become easier to find, understand and verify.",
  "about.problem.eyebrow": "Why Vesta",
  "about.problem.title":
    "Help exists. Finding the right way to it is often difficult.",
  "about.problem.text":
    "Services, responsibilities and access conditions are spread across many organisations. Vesta focuses on where digital support can realistically help: orientation, language and a clear next step.",
  "about.people.title": "For people",
  "about.people.text":
    "Less jargon, fewer detours and suitable services with visible sources and uncertainties.",
  "about.professionals.title": "For professionals",
  "about.professionals.text":
    "Less repeated research and a reliable shared knowledge base for referrals.",
  "about.system.title": "For Bern",
  "about.system.text":
    "Unsuccessful routes to help and missing services can become visible without creating personal profiles.",
  "about.responsibility.eyebrow": "Responsibility",
  "about.responsibility.title":
    "AI explains. Rules check. People take over.",
  "about.responsibility.text":
    "Vesta does not automate case decisions or allocate scarce places. AI may understand language and explain verified information. Safety, access and handoffs remain governed by transparent rules and accountable people.",
  "about.pilot.eyebrow": "Pilot project",
  "about.pilot.title": "Start small. Learn together.",
  "about.pilot.text":
    "The first prototype focuses on overnight shelter, basic needs and advice. It works without an account or case file. People with lived experience, professionals and organisations should help determine what is useful and safe.",
  "about.pilot.link": "View the project on GitHub",
  "about.pilot.note":
    "The technical prototype is publicly available. Feedback and participation are welcome.",
  "imprint.eyebrow": "Transparency",
  "imprint.title": "Legal notice",
  "imprint.project.label": "Project",
  "imprint.project.value": "Vesta – Bern social services guide",
  "imprint.status.label": "Status",
  "imprint.status.value": "Independent technical prototype in development",
  "imprint.responsibility.label": "Responsible organisation",
  "imprint.responsibility.value":
    "Not yet formally designated for public field use",
  "imprint.contact.label": "Project and feedback",
  "imprint.contact.value": "Vesta GitHub repository",
  "imprint.note":
    "Before public field use, the accountable contact, responsible organisation, privacy information and participating partners will be formally identified.",
  "privacy.eyebrow": "Transparency",
  "privacy.title": "Privacy notice",
  "privacy.lead":
    "Vesta is still in an early pilot phase. This page describes what data we currently process — deliberately as little as possible.",
  "privacy.scope.eyebrow": "What we process",
  "privacy.scope.title": "Only the details of your current search",
  "privacy.scope.text":
    "For a search, Vesta only processes the details you choose in the form: the selected area, your language, and optional details such as a dog, missing identity document, target group, age or safety flags. These details are only used for that one search.",
  "privacy.scope.noAccount":
    "Vesta works without an account. Your search is not stored as a case file or profile.",
  "privacy.location.eyebrow": "Optional location",
  "privacy.location.title": "Only with your explicit permission",
  "privacy.location.text":
    "If you select “Use my location”, Vesta rounds the browser position to about 100 metres and uses it only to calculate straight-line distance and sort equally suitable services. The position and calculated distances are neither stored nor sent to the AI model. The external Google Maps link contains only the service’s public destination, not your starting point.",
  "privacy.storage.eyebrow": "Storage",
  "privacy.storage.title": "No lasting storage of your search",
  "privacy.storage.text":
    "Your search details are sent to the Vesta API, used to work out the result, and are not saved in a database afterwards. No history of past searches is created.",
  "privacy.device.eyebrow": "On your device",
  "privacy.device.title": "Only your language preference",
  "privacy.device.text":
    "Vesta stores only your chosen language locally on your device, so the interface appears in the right language on your next visit. This detail never leaves your device.",
  "privacy.offline.eyebrow": "Offline use",
  "privacy.offline.title": "Offline storage holds no search results",
  "privacy.offline.text":
    "To allow installation as an app, Vesta caches technical parts such as the page shell, icons and fonts. Requests to the search API are explicitly excluded and are never cached.",
  "privacy.logs.eyebrow": "Technical logs",
  "privacy.logs.title": "Operational logs do not contain your full answers",
  "privacy.logs.text":
    "Like any web service, running the site creates technical logs, for example IP address, time and requested address, for security and troubleshooting. Retention period and deletion process will be formally defined before any public field use.",
  "privacy.offers.eyebrow": "Service register",
  "privacy.offers.title": "Public information about support services",
  "privacy.offers.text":
    "The service register contains verified, public information about support services in Bern — no personal data of users.",
  "privacy.ai.eyebrow": "AI",
  "privacy.ai.title": "AI language model in test operation",
  "privacy.ai.text":
    "Free text, approved questions and limited service facts are sent to OpenAI for interpretation and plain-language wording. AI does not decide access or allocate places. Do not enter names, addresses or contact details. Inputs, AI requests and responses, the intervening Vesta system logic and the displayed response are stored as one connected workflow until manually deleted and are only accessible to authorized administrators.",
  "privacy.hosting.eyebrow": "Hosting",
  "privacy.hosting.title": "Swiss infrastructure planned",
  "privacy.hosting.text":
    "Operation is planned on Swiss infrastructure. Before any public field use, the data processing agreement, subprocessors, storage locations and a data protection impact assessment will be formally clarified.",
  "privacy.rights.eyebrow": "Your rights",
  "privacy.rights.title": "Access, correction and deletion",
  "privacy.rights.text":
    "Because Vesta works without an account and keeps no search history, access, correction and deletion rights mainly concern technical logs. Please use the contact below for this.",
  "privacy.responsible.eyebrow": "Responsible organisation",
  "privacy.responsible.title": "Not yet formally designated",
  "privacy.responsible.text":
    "Vesta is currently an independent technical prototype. A responsible organisation for public field use has not yet been formally designated.",
  "privacy.contact.label": "Questions and feedback",
  "privacy.contact.value": "Vesta GitHub repository",
  "privacy.note":
    "This notice describes the current prototype state. Before any public field use, it will be formally completed with an accountable contact, a responsible organisation and verified subprocessors.",
  "footer.emergency":
    "Vesta does not replace emergency assistance and does not reserve places.",
  "footer.prototype":
    "Initial prototype · information not yet approved for field use",
  "footer.imprint": "About Vesta & legal notice",
  "footer.privacy": "Privacy notice",
  "offline.eyebrow": "No connection",
  "offline.title": "Vesta is currently offline.",
  "offline.body":
    "Without an internet connection, we deliberately do not show services that may be out of date. Reconnect and try again.",
  "offline.retry": "Try again",
  "offline.back": "Back to home",
  "dialogue.freeText.label": "Briefly describe what you need",
  "dialogue.freeText.placeholder": "e.g. I need a place to sleep tonight with my dog",
  "dialogue.freeText.submit": "Check suggestion",
  "dialogue.freeText.loading": "Checking …",
  "dialogue.interpretation.unclear":
    "I could not yet match your request to one area with confidence. Choose the most suitable area below.",
  "dialogue.interpretation.needApplied": "Recognized area: {need}",
  "dialogue.interpretation.confirmLegend": "Is this the right area?",
  "dialogue.needPicker.legend": "Choose an area",
  "dialogue.location.title": "Services near you",
  "dialogue.location.text":
    "Optional: use your approximate location to sort equally suitable services by proximity.",
  "dialogue.location.use": "Use my location",
  "dialogue.location.locating": "Finding your location…",
  "dialogue.location.active":
    "Your approximate location is being used for this search.",
  "dialogue.location.remove": "Stop using my location",
  "dialogue.location.denied":
    "Location permission was not granted. You can continue without location.",
  "dialogue.location.timeout":
    "Your location could not be found in time. You can continue without location.",
  "dialogue.location.unavailable":
    "Location is not available in this browser. You can continue without location.",
  "dialogue.start": "Start AI dialogue",
  "dialogue.loading": "Processing …",
  "dialogue.progress.label": "Progress through the support dialogue",
  "dialogue.progress.need": "Your need",
  "dialogue.progress.questions": "Questions",
  "dialogue.progress.results": "Services",
  "dialogue.progress.current": "current step",
  "dialogue.progress.complete": "complete",
  "dialogue.conversation.label": "Dialogue history",
  "dialogue.conversation.you": "You",
  "dialogue.conversation.vesta": "Vesta",
  "dialogue.conversation.selectedNeed": "Selected: {need}",
  "dialogue.conversation.interpreted":
    "I understand your need as “{need}”. Is that right?",
  "dialogue.conversation.answer": "Your answer: {answer}",
  "dialogue.conversation.resultsReady": "The relevant services are ready.",
  "dialogue.busy.interpreting.title": "Vesta is understanding your need",
  "dialogue.busy.interpreting.text":
    "Your input is being categorized. This usually takes only a moment.",
  "dialogue.busy.starting.title": "Vesta is preparing the next question",
  "dialogue.busy.starting.text":
    "The system logic is checking which detail still matters for a safe search.",
  "dialogue.busy.answer.title": "Vesta is checking your answer",
  "dialogue.busy.answer.text":
    "We are determining the next appropriate step and then checking possible services.",
  "dialogue.error.title": "Something went wrong",
  "dialogue.error": "The AI dialogue is currently unavailable.",
  "dialogue.question.eyebrow": "One more question",
  "dialogue.question.answerLegend": "Your answer",
  "dialogue.question.yes": "Yes",
  "dialogue.question.no": "No",
  "dialogue.question.numberLabel": "Your answer",
  "dialogue.question.numberSubmit": "Confirm",
  "dialogue.fit.gender.question":
    "Would a service specifically for women and FINTA people suit you?",
  "dialogue.fit.gender.help":
    "Some shelters are exclusively available to women and FINTA people.",
  "dialogue.fit.gender.yes": "Yes, that suits me",
  "dialogue.fit.gender.no": "No, I need a generally accessible service",
  "dialogue.fit.age.question": "Is the search for an adult?",
  "dialogue.fit.age.help":
    "Some overnight services are only available from the age of 18.",
  "dialogue.fit.age.adult": "Yes, aged 18 or older",
  "dialogue.fit.age.minor": "No, under 18",
  "dialogue.fit.decline": "Prefer not to say",
  "dialogue.result.eyebrow": "Explained result",
  "dialogue.result.title": "This may help you",
  "dialogue.restart": "Start over",
  "dialogue.other.title": "Something else",
  "dialogue.other.detail": "Describe it in your own words",
  "dialogue.back": "Back",
  "dialogue.interpretation.confirmHint": "Tap to continue",
};

const ar: Record<MessageKey, string> = {
  "a11y.skipToContent": "الانتقال مباشرة إلى المحتوى",
  "a11y.opensNewTab": "يفتح في علامة تبويب جديدة",
  "brand.homeLabel": "الصفحة الرئيسية لفيستا",
  "pilot.label": "مشروع تجريبي · برن",
  "nav.primaryLabel": "التنقل الرئيسي",
  "nav.home": "البحث",
  "nav.imprint": "معلومات قانونية",
  "nav.privacy": "الخصوصية",
  "locale.label": "لغة الواجهة",
  "locale.de": "Deutsch",
  "locale.fr": "Français",
  "locale.en": "English",
  "locale.ar": "العربية",
  "pwa.install": "تثبيت التطبيق",
  "hero.eyebrow": "دليل الخدمات الاجتماعية في برن",
  "hero.title": "ما الذي تحتاج إليه الآن؟",
  "hero.lead":
    "اعثر على خدمات اجتماعية مناسبة في برن بسهولة ومع عرض المصادر.",
  "hero.trust": "لا تحتاج إلى حساب. لا يُحفَظ بحثك كملف حالة.",
  "form.help":
    "أدخل فقط المعلومات المهمة لبحثك، ثم سنعرض الخدمات المحتملة.",
  "form.need.legend": "اختر مجالاً",
  "need.sleep.title": "مكان للنوم الليلة",
  "need.sleep.detail": "البحث عن مكان للمبيت",
  "need.basic.title": "الاحتياجات الأساسية",
  "need.basic.detail": "طعام أو استحمام أو إسعافات أولية",
  "need.counselling.title": "استشارة",
  "need.counselling.detail": "مساعدة بشأن الإدمان أو السكن أو المال",
  "form.targetGroup.label": "الفئة المستهدفة",
  "form.targetGroup.hint":
    "تساعد هذه المعلومة في تصنيف الخدمات ذات شروط الدخول الخاصة بشكل صحيح.",
  "form.targetGroup.none": "أفضل عدم الإجابة",
  "form.targetGroup.finta": "امرأة / FINTA",
  "form.targetGroup.other": "أخرى / بحث عام",
  "form.additional.legend": "معلومات إضافية",
  "form.dog": "لدي كلب",
  "form.noIdentity": "ليس لدي وثيقة هوية",
  "form.submit": "العثور على مساعدة مناسبة",
  "form.loading": "جارٍ التحقق من الخدمات…",
  "status.loading": "جارٍ التحقق من الخدمات.",
  "error.search":
    "البحث غير متاح حالياً. حاول مرة أخرى لاحقاً أو تواصل مباشرة مع شخص مختص.",
  "results.eyebrow": "النتيجة",
  "results.count.zero": "لا توجد خدمات تجريبية مطابقة",
  "results.count.one": "خدمة محتملة واحدة",
  "results.count.two": "خدمتان محتملتان",
  "results.count.few": "{count} خدمات محتملة",
  "results.count.many": "{count} خدمة محتملة",
  "results.count.other": "{count} خدمة محتملة",
  "results.demoBadge": "بيانات تجريبية · ليست للاستخدام الميداني",
  "availability.confirmed": "الحالة مؤكدة",
  "availability.call_to_confirm": "يرجى التحقق أولاً",
  "availability.unknown": "الحالة غير معروفة",
  "results.uncertainty": "يجب التحقق من بعض المعلومات.",
  "results.originalLanguage": "معلومات الخدمة الأصلية باللغة الألمانية",
  "results.checked": "تم التحقق آلياً في {date}",
  "results.source": "المصدر",
  "results.distance.meters": "نحو {distance} م بخط مستقيم",
  "results.distance.kilometers": "نحو {distance} كم بخط مستقيم",
  "results.address": "العنوان",
  "results.directions": "الاتجاهات في خرائط Google",
  "results.handoff":
    "لم نعثر على خدمة مناسبة بدرجة موثوقة. ينبغي أن يتولى شخص مختص متابعة الحالة.",
  "results.disclaimer":
    "لا تُحجز الخدمات تلقائياً. تحقّق مباشرة من حداثة المعلومات وبيانات الاتصال.",
  "principles.eyebrow": "كيف تعمل فيستا",
  "principles.title": "تقنية تسهّل الوصول.",
  "principle.verified.title": "معلومات متحقق منها",
  "principle.verified.text":
    "تعرض كل نتيجة مصدرها وتاريخ التحقق وأوجه عدم اليقين المتبقية.",
  "principle.rules.title": "قواعد واضحة",
  "principle.rules.text":
    "يتم التحقق من شروط الدخول بشفافية ولا يقررها الذكاء الاصطناعي.",
  "principle.handoff.title": "إحالة إلى شخص مختص",
  "principle.handoff.text":
    "عند وجود خطر أو عدم يقين أو بناءً على الطلب، يتولى شخص مختص المتابعة.",
  "about.back": "العودة إلى البحث عن المساعدة",
  "about.eyebrow": "حول فيستا والمعلومات القانونية",
  "about.title": "عقبات أقل في النظام. وصول أسهل إلى المساعدة.",
  "about.lead":
    "تطوّر فيستا بوابة موثوقة ومتعددة اللغات إلى منظومة الدعم في برن، لتصبح الخدمات المتاحة أسهل في العثور عليها وفهمها والتحقق منها.",
  "about.problem.eyebrow": "لماذا فيستا",
  "about.problem.title":
    "المساعدة موجودة، لكن الوصول إليها غالباً ما يكون معقداً.",
  "about.problem.text":
    "تتوزع الخدمات والمسؤوليات وشروط الوصول بين جهات عديدة. تركز فيستا على المجالات التي يمكن للدعم الرقمي أن يفيد فيها فعلياً: التوجيه واللغة وتوضيح الخطوة التالية.",
  "about.people.title": "للأشخاص",
  "about.people.text":
    "مصطلحات أقل تعقيداً وطرق أقصر وخدمات مناسبة مع إظهار المصادر وأوجه عدم اليقين.",
  "about.professionals.title": "للمختصين",
  "about.professionals.text":
    "وقت أقل للبحث المتكرر وقاعدة معلومات مشتركة وموثوقة للإحالة إلى الخدمات.",
  "about.system.title": "لمدينة برن",
  "about.system.text":
    "يمكن إظهار مسارات المساعدة غير الناجحة والخدمات الناقصة من دون إنشاء ملفات شخصية.",
  "about.responsibility.eyebrow": "المسؤولية",
  "about.responsibility.title":
    "الذكاء الاصطناعي يشرح. القواعد تتحقق. والأشخاص يتولون المسؤولية.",
  "about.responsibility.text":
    "لا تؤتمت فيستا القرارات المتعلقة بالحالات ولا توزع الأماكن المحدودة. يمكن للذكاء الاصطناعي فهم اللغة وشرح المعلومات المتحقق منها، بينما تبقى السلامة والوصول والإحالة خاضعة لقواعد واضحة ولمسؤولية بشرية.",
  "about.pilot.eyebrow": "مشروع تجريبي",
  "about.pilot.title": "نبدأ بخطوات صغيرة ونتعلم معاً.",
  "about.pilot.text":
    "يركز النموذج الأولي على المبيت والاحتياجات الأساسية والاستشارة. ويعمل من دون حساب أو ملف حالة. يجب أن يشارك أصحاب التجربة والمختصون والمنظمات في تحديد ما هو مفيد وآمن.",
  "about.pilot.link": "عرض المشروع على GitHub",
  "about.pilot.note":
    "النموذج التقني متاح للاطلاع العام، ونرحب بالملاحظات والمشاركة.",
  "imprint.eyebrow": "الشفافية",
  "imprint.title": "المعلومات القانونية",
  "imprint.project.label": "المشروع",
  "imprint.project.value": "فيستا – دليل الخدمات الاجتماعية في برن",
  "imprint.status.label": "الحالة",
  "imprint.status.value": "نموذج تقني أولي مستقل قيد التطوير",
  "imprint.responsibility.label": "الجهة المسؤولة",
  "imprint.responsibility.value":
    "لم تُحدَّد رسمياً بعد للاستخدام الميداني العام",
  "imprint.contact.label": "المشروع والملاحظات",
  "imprint.contact.value": "مستودع فيستا على GitHub",
  "imprint.note":
    "قبل أي استخدام ميداني عام، ستُحدَّد رسمياً جهة الاتصال المسؤولة والجهة المشغلة ومعلومات الخصوصية والشركاء المشاركون.",
  "privacy.eyebrow": "الشفافية",
  "privacy.title": "إشعار الخصوصية",
  "privacy.lead":
    "لا تزال فيستا في مرحلة تجريبية مبكرة. توضح هذه الصفحة البيانات التي نعالجها حالياً - وهي بيانات قليلة عمداً.",
  "privacy.scope.eyebrow": "ما الذي نعالجه",
  "privacy.scope.title": "فقط معلومات بحثك الحالي",
  "privacy.scope.text":
    "عند إجراء بحث، تعالج فيستا فقط المعلومات التي تختارها في النموذج: المجال المختار، لغتك، ومعلومات اختيارية مثل وجود كلب، أو عدم وجود وثيقة هوية، أو الفئة المستهدفة، أو العمر، أو مؤشرات السلامة. تُستخدم هذه المعلومات فقط لهذا البحث.",
  "privacy.scope.noAccount":
    "تعمل فيستا من دون حساب. لا يُحفَظ بحثك كملف حالة أو ملف شخصي.",
  "privacy.location.eyebrow": "الموقع الاختياري",
  "privacy.location.title": "فقط بعد موافقتك الصريحة",
  "privacy.location.text":
    "إذا اخترت «استخدام موقعي»، تقرّب فيستا موقع المتصفح إلى نحو 100 متر وتستخدمه فقط لحساب المسافة بخط مستقيم وترتيب الخدمات المتساوية في الملاءمة. لا يُحفَظ الموقع ولا المسافات المحسوبة ولا تُرسل إلى نموذج الذكاء الاصطناعي. يحتوي رابط خرائط Google الخارجي فقط على الوجهة العامة للخدمة، وليس نقطة انطلاقك.",
  "privacy.storage.eyebrow": "التخزين",
  "privacy.storage.title": "لا يُحفَظ بحثك بشكل دائم",
  "privacy.storage.text":
    "تُرسَل معلومات بحثك إلى واجهة برمجة تطبيقات فيستا، وتُستخدم لتقييم النتيجة، ولا تُحفَظ بعد ذلك في قاعدة بيانات. لا يُنشأ أي سجل لعمليات بحث سابقة.",
  "privacy.device.eyebrow": "على جهازك",
  "privacy.device.title": "فقط تفضيل اللغة",
  "privacy.device.text":
    "تُخزّن فيستا محلياً على جهازك اللغة التي اخترتها فقط، حتى تظهر الواجهة باللغة الصحيحة في زيارتك القادمة. لا تغادر هذه المعلومة جهازك أبداً.",
  "privacy.offline.eyebrow": "الاستخدام دون اتصال",
  "privacy.offline.title": "لا يحتوي التخزين دون اتصال على نتائج بحث",
  "privacy.offline.text":
    "لتمكين التثبيت كتطبيق، تخزّن فيستا مؤقتاً عناصر تقنية مثل هيكل الصفحة والأيقونات والخطوط. تُستثنى طلبات واجهة برمجة تطبيقات البحث من ذلك صراحةً ولا تُخزَّن مؤقتاً أبداً.",
  "privacy.logs.eyebrow": "السجلات التقنية",
  "privacy.logs.title": "سجلات التشغيل لا تحتوي على إجاباتك الكاملة",
  "privacy.logs.text":
    "كما هو الحال مع أي خدمة ويب، ينشئ تشغيل الموقع سجلات تقنية، مثل عنوان IP والوقت والعنوان المطلوب، لأغراض الأمان واستكشاف الأخطاء. سيتم تحديد مدة الاحتفاظ وعملية الحذف بشكل ملزم قبل أي استخدام ميداني عام.",
  "privacy.offers.eyebrow": "سجل الخدمات",
  "privacy.offers.title": "معلومات عامة عن خدمات المساعدة",
  "privacy.offers.text":
    "يحتوي سجل الخدمات على معلومات عامة تم التحقق منها حول خدمات المساعدة في برن - ولا يحتوي على بيانات شخصية للمستخدمين.",
  "privacy.ai.eyebrow": "الذكاء الاصطناعي",
  "privacy.ai.title": "نموذج الذكاء الاصطناعي في مرحلة الاختبار",
  "privacy.ai.text":
    "تُرسل النصوص الحرة والأسئلة المعتمدة ومعلومات محدودة عن الخدمات إلى OpenAI للتفسير والصياغة الواضحة. لا يقرر الذكاء الاصطناعي الوصول إلى الخدمات ولا يخصص أماكن. لا تُدخل أسماء أو عناوين أو بيانات اتصال. تُحفظ المدخلات وطلبات الذكاء الاصطناعي وردوده ومنطق نظام Vesta الوسيط والرد المعروض كسير عمل مترابط إلى أن تُحذف يدويًا، ولا يمكن الاطلاع عليها إلا من قِبل المسؤولين المخوَّلين.",
  "privacy.hosting.eyebrow": "الاستضافة",
  "privacy.hosting.title": "يُخطَّط لبنية تحتية سويسرية",
  "privacy.hosting.text":
    "من المخطط تشغيل الخدمة على بنية تحتية سويسرية. قبل أي استخدام ميداني عام، سيتم تحديد اتفاقية معالجة البيانات والجهات الفرعية المعالِجة ومواقع التخزين وتقييم الأثر على حماية البيانات بشكل ملزم.",
  "privacy.rights.eyebrow": "حقوقك",
  "privacy.rights.title": "الاطلاع والتصحيح والحذف",
  "privacy.rights.text":
    "بما أن فيستا تعمل من دون حساب ولا تحتفظ بسجل بحث، فإن حقوق الاطلاع والتصحيح والحذف تتعلق بشكل أساسي بالسجلات التقنية. يرجى التواصل عبر جهة الاتصال أدناه لهذا الغرض.",
  "privacy.responsible.eyebrow": "الجهة المسؤولة",
  "privacy.responsible.title": "لم تُحدَّد رسمياً بعد",
  "privacy.responsible.text":
    "فيستا حالياً نموذج تقني أولي مستقل. لم تُحدَّد بعد رسمياً جهة مسؤولة عن الاستخدام الميداني العام.",
  "privacy.contact.label": "الأسئلة والملاحظات",
  "privacy.contact.value": "مستودع فيستا على GitHub",
  "privacy.note":
    "يصف هذا الإشعار حالة النموذج الأولي الحالية. قبل أي استخدام ميداني عام، سيُستكمَل بشكل ملزم بجهة اتصال مسؤولة وجهة مشغّلة وجهات معالجة فرعية تم التحقق منها.",
  "footer.emergency": "لا تحل فيستا محل خدمات الطوارئ ولا تحجز أماكن.",
  "footer.prototype":
    "نموذج أولي · المعلومات غير معتمدة بعد للاستخدام الميداني",
  "footer.imprint": "حول فيستا والمعلومات القانونية",
  "footer.privacy": "إشعار الخصوصية",
  "offline.eyebrow": "لا يوجد اتصال",
  "offline.title": "فيستا غير متصلة بالإنترنت حالياً.",
  "offline.body":
    "من دون اتصال بالإنترنت لا نعرض عمداً خدمات قد تكون معلوماتها قديمة. أعد الاتصال وحاول مرة أخرى.",
  "offline.retry": "إعادة المحاولة",
  "offline.back": "العودة إلى الصفحة الرئيسية",
  "dialogue.freeText.label": "صف باختصار ما تحتاجه",
  "dialogue.freeText.placeholder": "مثال: أحتاج مكانًا للنوم الليلة مع كلبي",
  "dialogue.freeText.submit": "التحقق من الاقتراح",
  "dialogue.freeText.loading": "جارٍ التحقق…",
  "dialogue.interpretation.unclear":
    "لم أتمكن بعد من تحديد المجال المناسب لطلبك بوضوح. اختر المجال الأنسب أدناه.",
  "dialogue.interpretation.needApplied": "المجال الذي تم التعرف عليه: {need}",
  "dialogue.interpretation.confirmLegend": "هل هذا هو المجال المناسب؟",
  "dialogue.needPicker.legend": "اختر مجالاً",
  "dialogue.location.title": "خدمات قريبة منك",
  "dialogue.location.text":
    "اختياري: استخدم موقعك التقريبي لترتيب الخدمات المتساوية في الملاءمة حسب القرب.",
  "dialogue.location.use": "استخدام موقعي",
  "dialogue.location.locating": "جارٍ تحديد موقعك…",
  "dialogue.location.active": "يُستخدم موقعك التقريبي لهذا البحث.",
  "dialogue.location.remove": "إيقاف استخدام موقعي",
  "dialogue.location.denied":
    "لم تمنح إذن الموقع. يمكنك المتابعة من دون موقع.",
  "dialogue.location.timeout":
    "تعذر تحديد موقعك في الوقت المناسب. يمكنك المتابعة من دون موقع.",
  "dialogue.location.unavailable":
    "تحديد الموقع غير متاح في هذا المتصفح. يمكنك المتابعة من دون موقع.",
  "dialogue.start": "بدء حوار الذكاء الاصطناعي",
  "dialogue.loading": "جارٍ المعالجة…",
  "dialogue.progress.label": "التقدم في حوار المساعدة",
  "dialogue.progress.need": "طلبك",
  "dialogue.progress.questions": "أسئلة",
  "dialogue.progress.results": "العروض",
  "dialogue.progress.current": "الخطوة الحالية",
  "dialogue.progress.complete": "مكتمل",
  "dialogue.conversation.label": "مسار الحوار",
  "dialogue.conversation.you": "أنت",
  "dialogue.conversation.vesta": "فيستا",
  "dialogue.conversation.selectedNeed": "تم الاختيار: {need}",
  "dialogue.conversation.interpreted":
    "أفهم طلبك على أنه «{need}». هل هذا صحيح؟",
  "dialogue.conversation.answer": "إجابتك: {answer}",
  "dialogue.conversation.resultsReady": "العروض المناسبة جاهزة.",
  "dialogue.busy.interpreting.title": "فيستا يفهم طلبك",
  "dialogue.busy.interpreting.text":
    "يجري تصنيف مدخلاتك، وعادة لا يستغرق ذلك سوى لحظة.",
  "dialogue.busy.starting.title": "فيستا يحضّر السؤال التالي",
  "dialogue.busy.starting.text":
    "يتحقق منطق النظام من المعلومة الإضافية المهمة لبحث آمن.",
  "dialogue.busy.answer.title": "فيستا يتحقق من إجابتك",
  "dialogue.busy.answer.text":
    "نحدد الخطوة المناسبة التالية ثم نتحقق من العروض الممكنة.",
  "dialogue.error.title": "حدث خطأ",
  "dialogue.error": "حوار الذكاء الاصطناعي غير متاح حاليًا.",
  "dialogue.question.eyebrow": "سؤال آخر",
  "dialogue.question.answerLegend": "إجابتك",
  "dialogue.question.yes": "نعم",
  "dialogue.question.no": "لا",
  "dialogue.question.numberLabel": "إجابتك",
  "dialogue.question.numberSubmit": "تأكيد",
  "dialogue.fit.gender.question":
    "هل يناسبك عرض مخصص للنساء ولأشخاص FINTA؟",
  "dialogue.fit.gender.help":
    "بعض أماكن الإيواء متاحة حصريًا للنساء ولأشخاص FINTA.",
  "dialogue.fit.gender.yes": "نعم، هذا يناسبني",
  "dialogue.fit.gender.no": "لا، أبحث عن عرض متاح للجميع",
  "dialogue.fit.age.question": "هل البحث يخص شخصًا بالغًا؟",
  "dialogue.fit.age.help":
    "بعض أماكن المبيت متاحة فقط لمن يبلغون 18 عامًا أو أكثر.",
  "dialogue.fit.age.adult": "نعم، 18 عامًا أو أكثر",
  "dialogue.fit.age.minor": "لا، أقل من 18 عامًا",
  "dialogue.fit.decline": "أفضل عدم ذكر ذلك",
  "dialogue.result.eyebrow": "نتيجة موضحة",
  "dialogue.result.title": "قد تساعدك هذه العروض",
  "dialogue.restart": "البدء من جديد",
  "dialogue.other.title": "شيء آخر",
  "dialogue.other.detail": "صفه بكلماتك الخاصة",
  "dialogue.back": "رجوع",
  "dialogue.interpretation.confirmHint": "اضغط للمتابعة",
};

export const messages: Record<Locale, Record<MessageKey, string>> = {
  de,
  fr,
  en,
  ar,
};

export const defaultLocale: Locale = "de";

export const localeTags: Record<Locale, string> = {
  de: "de-CH",
  fr: "fr-CH",
  en: "en-GB",
  ar: "ar",
};

export function normalizeLocale(value: string | null | undefined): Locale | null {
  if (!value) {
    return null;
  }

  const language = value.toLowerCase().split("-")[0];
  return supportedLocales.find((locale) => locale === language) ?? null;
}

export function getDirection(locale: Locale): "ltr" | "rtl" {
  return locale === "ar" ? "rtl" : "ltr";
}

export function interpolate(
  message: string,
  values: Record<string, string | number> = {},
): string {
  return message.replace(/\{(\w+)\}/g, (_, key: string) =>
    Object.hasOwn(values, key) ? String(values[key]) : `{${key}}`,
  );
}

export function resultCountKey(locale: Locale, count: number): MessageKey {
  const category = new Intl.PluralRules(localeTags[locale]).select(count);
  return `results.count.${category}` as MessageKey;
}
