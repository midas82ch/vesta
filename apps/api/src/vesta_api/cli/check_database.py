import os
from pathlib import Path

import psycopg

ROLE_EXPECTATIONS = {
    "vesta_app": {
        ("public.offers", "SELECT"): True,
        ("public.offers", "INSERT"): False,
        ("public.offer_verifications", "UPDATE"): False,
        ("public.offer_ingestion_runs", "INSERT"): False,
    },
    "vesta_ingest": {
        ("public.offers", "SELECT"): True,
        ("public.offers", "INSERT"): True,
        ("public.offer_categories", "DELETE"): True,
        ("public.offer_ingestion_runs", "INSERT"): True,
    },
}


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

            expectations = ROLE_EXPECTATIONS.get(user, {})
            failed = False
            for (table_name, privilege), expected in expectations.items():
                cursor.execute(
                    "SELECT has_table_privilege(current_user, %s, %s)",
                    (table_name, privilege),
                )
                result = cursor.fetchone()
                actual = bool(result and result[0])
                print(
                    f"privilege table={table_name} operation={privilege} "
                    f"granted={'yes' if actual else 'no'}"
                )
                failed = failed or actual is not expected

            cursor.execute(
                "SELECT has_schema_privilege(current_user, 'public', 'CREATE')"
            )
            schema_result = cursor.fetchone()
            can_create_schema_objects = bool(schema_result and schema_result[0])
            if user in ROLE_EXPECTATIONS:
                print(
                    "privilege schema=public operation=CREATE "
                    f"granted={'yes' if can_create_schema_objects else 'no'}"
                )
                failed = failed or can_create_schema_objects

            if failed:
                raise SystemExit("Database role privileges do not match expectations")


if __name__ == "__main__":
    main()
