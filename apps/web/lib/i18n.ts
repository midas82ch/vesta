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
  "footer.emergency": "Vesta ersetzt keine Notfallhilfe und reserviert keine Plätze.",
  "footer.prototype":
    "Initialer Prototyp · Angaben noch nicht für den Feldeinsatz freigegeben",
  "footer.imprint": "Über Vesta & Impressum",
  "offline.eyebrow": "Keine Verbindung",
  "offline.title": "Vesta ist gerade offline.",
  "offline.body":
    "Ohne Internetverbindung zeigen wir bewusst keine möglicherweise veralteten Angebote. Stelle die Verbindung wieder her und versuche es erneut.",
  "offline.retry": "Erneut versuchen",
  "offline.back": "Zur Startseite",
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
  "footer.emergency":
    "Vesta ne remplace pas l’aide d’urgence et ne réserve aucune place.",
  "footer.prototype":
    "Prototype initial · informations non encore autorisées pour le terrain",
  "footer.imprint": "À propos & mentions légales",
  "offline.eyebrow": "Pas de connexion",
  "offline.title": "Vesta est actuellement hors ligne.",
  "offline.body":
    "Sans connexion internet, nous n’affichons volontairement aucune offre potentiellement obsolète. Rétablis la connexion et réessaie.",
  "offline.retry": "Réessayer",
  "offline.back": "Retour à l’accueil",
};

const en: Record<MessageKey, string> = {
  "a11y.skipToContent": "Skip to content",
  "a11y.opensNewTab": "opens in a new tab",
  "brand.homeLabel": "Vesta home page",
  "pilot.label": "Pilot · Bern",
  "nav.primaryLabel": "Main navigation",
  "nav.home": "Search",
  "nav.imprint": "Imprint",
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
  "footer.emergency":
    "Vesta does not replace emergency assistance and does not reserve places.",
  "footer.prototype":
    "Initial prototype · information not yet approved for field use",
  "footer.imprint": "About Vesta & legal notice",
  "offline.eyebrow": "No connection",
  "offline.title": "Vesta is currently offline.",
  "offline.body":
    "Without an internet connection, we deliberately do not show services that may be out of date. Reconnect and try again.",
  "offline.retry": "Try again",
  "offline.back": "Back to home",
};

const ar: Record<MessageKey, string> = {
  "a11y.skipToContent": "الانتقال مباشرة إلى المحتوى",
  "a11y.opensNewTab": "يفتح في علامة تبويب جديدة",
  "brand.homeLabel": "الصفحة الرئيسية لفيستا",
  "pilot.label": "مشروع تجريبي · برن",
  "nav.primaryLabel": "التنقل الرئيسي",
  "nav.home": "البحث",
  "nav.imprint": "معلومات قانونية",
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
  "footer.emergency": "لا تحل فيستا محل خدمات الطوارئ ولا تحجز أماكن.",
  "footer.prototype":
    "نموذج أولي · المعلومات غير معتمدة بعد للاستخدام الميداني",
  "footer.imprint": "حول فيستا والمعلومات القانونية",
  "offline.eyebrow": "لا يوجد اتصال",
  "offline.title": "فيستا غير متصلة بالإنترنت حالياً.",
  "offline.body":
    "من دون اتصال بالإنترنت لا نعرض عمداً خدمات قد تكون معلوماتها قديمة. أعد الاتصال وحاول مرة أخرى.",
  "offline.retry": "إعادة المحاولة",
  "offline.back": "العودة إلى الصفحة الرئيسية",
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
