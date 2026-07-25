import os
from pathlib import Path

import psycopg


def main() -> None:
    database_url_file = Path(
        os.environ.get("DATABASE_URL_FILE", "/run/secrets/database-url")
    )
    database_url = database_url_file.read_text(encoding="utf-8").strip()

    with psycopg.connect(database_url, connect_timeout=8) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    current_setting('server_version'),
                    current_setting('ssl')
                """
            )
            database, user, version, ssl_enabled = cursor.fetchone()
            print(
                f"connection database={database} user={user} "
                f"version={version} ssl={ssl_enabled}"
            )

            cursor.execute(
                """
                SELECT name, default_version, installed_version
                FROM pg_available_extensions
                WHERE name IN ('postgis', 'vector')
                ORDER BY name
                """
            )
            extensions = cursor.fetchall()
            if not extensions:
                print("extensions unavailable")
            for name, available, installed in extensions:
                print(
                    f"extension name={name} available={available} "
                    f"installed={installed or 'no'}"
                )


if __name__ == "__main__":
    main()
