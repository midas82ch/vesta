type OfferServiceSelection = {
  needs: string[];
  services: string[];
};

type ServiceSummary = {
  key: string;
  service_group: "basic_needs" | "counselling" | "addiction";
  status: "draft" | "published" | "archived";
};

type CategorySummary = {
  key: string;
  localizations: Record<string, { title: string }>;
};

export function missingServiceRequirementMessage(
  offer: OfferServiceSelection,
  services: ServiceSummary[],
  categories: CategorySummary[],
) {
  const publishedServices = new Map(
    services
      .filter((service) => service.status === "published")
      .map((service) => [service.key, service]),
  );
  const selectedServices = offer.services
    .map((key) => publishedServices.get(key))
    .filter((service): service is ServiceSummary => service !== undefined);
  const selectedGroups = new Set(selectedServices.map((service) => service.service_group));
  const selectedKeys = new Set(selectedServices.map((service) => service.key));
  const missingNeeds = offer.needs.filter((need) => {
    if (need === "basic_needs") return !selectedGroups.has("basic_needs");
    if (need === "counselling") return !selectedGroups.has("counselling");
    if (need === "daytime_stay") return !selectedKeys.has("daytime_no_purchase");
    return false;
  });
  const categoryNames = missingNeeds.map((need) => {
    const category = categories.find((item) => item.key === need);
    return category?.localizations.de?.title ?? need;
  });

  if (categoryNames.length === 0) {
    return "Veröffentlichung noch nicht möglich: Mindestens eine erforderliche Leistung ist nicht aktiv. Prüfen Sie im Abschnitt „Quellenbelegte Leistungen“ die Auswahl, speichern Sie den Entwurf und versuchen Sie es erneut.";
  }

  const quotedNames = categoryNames.map((name) => `„${name}“`);
  const readableNames = quotedNames.length === 1
    ? quotedNames[0]
    : `${quotedNames.slice(0, -1).join(", ")} und ${quotedNames.at(-1)}`;
  const subject = categoryNames.length === 1
    ? `Für die Kategorie ${readableNames} fehlt eine passende, aktive Leistung.`
    : `Für die Kategorien ${readableNames} fehlen passende, aktive Leistungen.`;
  return `Veröffentlichung noch nicht möglich: ${subject} Wählen Sie weiter unten unter „Quellenbelegte Leistungen“ für jede genannte Kategorie mindestens eine Leistung aus, die ausdrücklich in der Quelle belegt ist. Speichern Sie danach den Entwurf und klicken Sie erneut auf „Veröffentlichen“.`;
}
