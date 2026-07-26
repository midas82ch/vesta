"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui";

export default function AdminLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) {
        setError(
          response.status === 429
            ? "Zu viele Anmeldeversuche. Bitte später erneut versuchen."
            : "Benutzername oder Passwort ist falsch.",
        );
        return;
      }
      router.push("/admin/ai-audit");
      router.refresh();
    } catch {
      setError("Anmeldung derzeit nicht möglich.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="admin-login-shell">
      <div className="navigator-card">
        <h1>Admin-Login</h1>
        <form aria-busy={busy} onSubmit={handleSubmit}>
          <label className="field" htmlFor="admin-username">
            Benutzername
            <input
              aria-describedby={error ? "admin-login-error" : undefined}
              aria-invalid={Boolean(error)}
              autoComplete="username"
              id="admin-username"
              onChange={(event) => {
                setUsername(event.target.value);
                setError(null);
              }}
              required
              value={username}
            />
          </label>
          <label className="field" htmlFor="admin-password">
            Passwort
            <input
              aria-describedby={error ? "admin-login-error" : undefined}
              aria-invalid={Boolean(error)}
              autoComplete="current-password"
              id="admin-password"
              onChange={(event) => {
                setPassword(event.target.value);
                setError(null);
              }}
              required
              type="password"
              value={password}
            />
          </label>
          {error && (
            <p className="error-message" id="admin-login-error" role="alert">
              {error}
            </p>
          )}
          <Button disabled={busy} type="submit">
            {busy ? "Anmelden …" : "Anmelden"}
          </Button>
        </form>
      </div>
    </main>
  );
}
