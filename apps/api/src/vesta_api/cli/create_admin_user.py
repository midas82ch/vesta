"""Interactively create (or update) an admin_users row.

Run against the admin database connection, e.g.:

    docker compose run --rm --no-deps migrate \
        python -m vesta_api.cli.create_admin_user
"""

import getpass
import os
from pathlib import Path

from vesta_api.repositories.admin_users import PostgresAdminUserRepository
from vesta_api.security import hash_password


def _read_admin_url() -> str:
    secret_path = Path(
        os.environ.get("DATABASE_ADMIN_URL_FILE", "/run/secrets/database-admin-url")
    )
    return secret_path.read_text(encoding="utf-8").strip()


def _prompt_credentials() -> tuple[str, str]:
    username = input("Admin-Benutzername: ").strip()
    if not username:
        raise SystemExit("Benutzername darf nicht leer sein")

    password = getpass.getpass("Passwort: ")
    confirm = getpass.getpass("Passwort wiederholen: ")
    if password != confirm:
        raise SystemExit("Passwoerter stimmen nicht ueberein")
    if len(password) < 12:
        raise SystemExit("Passwort muss mindestens 12 Zeichen lang sein")
    return username, password


def main() -> None:
    admin_url = _read_admin_url()
    username, password = _prompt_credentials()

    repository = PostgresAdminUserRepository(admin_url)
    try:
        existing = repository.get_by_username(username)
        if existing is not None:
            raise SystemExit(
                f"Admin-Benutzer '{username}' existiert bereits "
                "(Aktualisieren ist ueber dieses Skript nicht vorgesehen)."
            )
        repository.create(username=username, password_hash=hash_password(password))
        print(f"Admin-Benutzer '{username}' wurde angelegt.")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
