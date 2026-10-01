import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const componentPath = new URL("../components/dialogue-form.tsx", import.meta.url);
const stylesPath = new URL("../app/globals.css", import.meta.url);
const iconGridPath = new URL("../components/ui/icon-choice-grid.tsx", import.meta.url);

test("public result cards show service information without AI reasoning", async () => {
  const component = await readFile(componentPath, "utf8");

  assert.match(component, /candidate\.offer\.summary/);
  assert.match(component, /candidate\.offer\.contact_note/);
  assert.match(component, /candidate\.offer\.source\.url/);
  assert.match(component, /interpretation\.service_topics \?\? \[\]/);
  assert.doesNotMatch(component, /explanation\.headline/);
  assert.doesNotMatch(component, /explanation\.reasons/);
  assert.doesNotMatch(component, /dialogue\.result\.eyebrow/);
});

test("result actions are touch-friendly and mobile-first", async () => {
  const styles = await readFile(stylesPath, "utf8");

  assert.match(styles, /\.result-actions\s*\{[^}]*display:\s*grid/s);
  assert.match(styles, /\.directions-link,\s*\.offer-link\s*\{[^}]*min-height:\s*44px/s);
  assert.match(
    styles,
    /@media \(min-width: 30rem\)\s*\{[^}]*\.result-actions\s*\{[^}]*grid-template-columns/s,
  );
});

test("service choices use an accessible two-column mobile icon grid", async () => {
  const [styles, component] = await Promise.all([
    readFile(stylesPath, "utf8"),
    readFile(iconGridPath, "utf8"),
  ]);

  assert.match(styles, /\.icon-choice-grid\s*\{[^}]*grid-template-columns:\s*repeat\(2,/s);
  assert.match(styles, /\.icon-choice-item\s*\{[^}]*min-height:\s*116px/s);
  assert.match(styles, /@media \(min-width:\s*42rem\)[\s\S]*repeat\(3,/);
  assert.match(styles, /@media \(min-width:\s*64rem\)[\s\S]*repeat\(4,/);
  assert.match(component, /aria-pressed=\{selected\}/);
  assert.match(component, /<span>\{option\.label\}<\/span>/);
  assert.doesNotMatch(component, /type="checkbox"/);
});
