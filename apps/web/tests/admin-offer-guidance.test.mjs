import assert from "node:assert/strict";
import test from "node:test";

import { missingServiceRequirementMessage } from "../lib/admin-offer-guidance.ts";

const categories = [
  { key: "basic_needs", localizations: { de: { title: "Grundversorgung" } } },
  { key: "counselling", localizations: { de: { title: "Beratung" } } },
  { key: "daytime_stay", localizations: { de: { title: "Aufenthalt & Toilette" } } },
];

const services = [
  { key: "meal", service_group: "basic_needs", status: "published" },
  { key: "general_social", service_group: "counselling", status: "published" },
  { key: "daytime_no_purchase", service_group: "basic_needs", status: "published" },
  { key: "toilet_draft", service_group: "basic_needs", status: "draft" },
];

test("names the category whose active source-backed service is missing", () => {
  const message = missingServiceRequirementMessage(
    { needs: ["basic_needs"], services: [] },
    services,
    categories,
  );

  assert.match(message, /Kategorie „Grundversorgung“/);
  assert.match(message, /Quellenbelegte Leistungen/);
  assert.match(message, /Entwurf/);
  assert.match(message, /„Veröffentlichen“/);
});

test("does not treat a draft service as active", () => {
  const message = missingServiceRequirementMessage(
    { needs: ["basic_needs"], services: ["toilet_draft"] },
    services,
    categories,
  );

  assert.match(message, /Kategorie „Grundversorgung“/);
});

test("names every category that still needs an active service", () => {
  const message = missingServiceRequirementMessage(
    { needs: ["basic_needs", "counselling"], services: [] },
    services,
    categories,
  );

  assert.match(message, /Kategorien „Grundversorgung“ und „Beratung“/);
});

test("requires the dedicated daytime service for Aufenthalt & Toilette", () => {
  const message = missingServiceRequirementMessage(
    { needs: ["daytime_stay"], services: ["meal"] },
    services,
    categories,
  );

  assert.match(message, /Kategorie „Aufenthalt & Toilette“/);
});
