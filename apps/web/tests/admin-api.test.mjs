import assert from "node:assert/strict";
import test from "node:test";

import { isAllowedAdminMutationOrigin } from "../lib/admin-origin.ts";

test("accepts the public origin forwarded to the internal Next server", () => {
  const request = new Request("http://localhost:3000/api/admin/categories", {
    method: "POST",
    headers: {
      host: "www.vesta-app.ch",
      origin: "https://www.vesta-app.ch",
      "x-forwarded-proto": "https",
    },
  });

  assert.equal(isAllowedAdminMutationOrigin(request), true);
});

test("accepts the direct same-origin host even when the request URL is normalized", () => {
  const request = new Request("http://localhost:3000/api/admin/categories", {
    method: "POST",
    headers: {
      host: "127.0.0.1:3000",
      origin: "http://127.0.0.1:3000",
    },
  });

  assert.equal(isAllowedAdminMutationOrigin(request), true);
});

test("rejects missing and cross-site origins", () => {
  const missingOrigin = new Request(
    "https://www.vesta-app.ch/api/admin/categories",
    { method: "POST", headers: { host: "www.vesta-app.ch" } },
  );
  const crossSite = new Request(
    "https://www.vesta-app.ch/api/admin/categories",
    {
      method: "POST",
      headers: {
        host: "www.vesta-app.ch",
        origin: "https://attacker.example",
      },
    },
  );

  assert.equal(isAllowedAdminMutationOrigin(missingOrigin), false);
  assert.equal(isAllowedAdminMutationOrigin(crossSite), false);
});
