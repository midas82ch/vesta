import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

import psycopg
from psycopg import sql


@dataclass(frozen=True)
class DatabaseRole:
    username: str
    secret_filename: str
    table_privileges: dict[str, tuple[str, ...]]


ROLES = (
    DatabaseRole(
        username="vesta_app",
        secret_filename="database-url",
        table_privileges={
            "organizations": ("SELECT",),
            "offers": ("SELECT",),
            "offer_categories": ("SELECT",),
            "offer_verifications": ("SELECT",),
            "need_definitions": ("SELECT",),
            "need_localizations": ("SELECT",),
            "attribute_definitions": ("SELECT",),
            "attribute_options": ("SELECT",),
            "attribute_option_localizations": ("SELECT",),
            "question_definitions": ("SELECT",),
            "question_localizations": ("SELECT",),
        },
    ),
    DatabaseRole(
        username="vesta_ingest",
        secret_filename="database-ingest-url",
        table_privileges={
            "organizations": ("SELECT", "INSERT", "UPDATE"),
            "offers": ("SELECT", "INSERT", "UPDATE"),
            "offer_categories": ("SELECT", "INSERT", "DELETE"),
            "offer_verifications": ("SELECT", "INSERT", "UPDATE"),
            "offer_ingestion_runs": ("INSERT",),
        },
    ),
)


def database_url_for_user(admin_url: str, username: str, password: str) -> str:
    parsed = urlsplit(admin_url)
    hostname = parsed.hostname or ""
    if ":" in hostname:
        hostname = f"[{hostname}]"
    host = f"{hostname}:{parsed.port}" if parsed.port else hostname
    netloc = f"{quote(username, safe='')}:{quote(password, safe='')}@{host}"
    return urlunsplit(
        (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )


def _password_from_url(database_url: str) -> str:
    password = urlsplit(database_url).password
    if not password:
        raise RuntimeError("Existing role secret does not contain a password")
    return unquote(password)


def _role_exists(connection: psycopg.Connection, username: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)",
            (username,),
        )
        result = cursor.fetchone()
    return bool(result and result[0])


def _ensure_login_role(
    connection: psycopg.Connection,
    username: str,
    password: str,
    *,
    reset_password: bool,
) -> None:
    role_identifier = sql.Identifier(username)
    password_literal = sql.Literal(password)
    role_options = sql.SQL(
        "LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION"
    )

    if _role_exists(connection, username):
        if reset_password:
            connection.execute(
                sql.SQL("ALTER ROLE {} WITH {} PASSWORD {}").format(
                    role_identifier,
                    role_options,
                    password_literal,
                )
            )
        else:
            connection.execute(
                sql.SQL("ALTER ROLE {} WITH {}").format(
                    role_identifier,
                    role_options,
                )
            )
    else:
        connection.execute(
            sql.SQL("CREATE ROLE {} WITH {} PASSWORD {}").format(
                role_identifier,
                role_options,
                password_literal,
            )
        )


def _apply_privileges(
    connection: psycopg.Connection,
    role: DatabaseRole,
    database_name: str,
) -> None:
    role_identifier = sql.Identifier(role.username)
    connection.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
            sql.Identifier(database_name),
            role_identifier,
        )
    )
    connection.execute(
        sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role_identifier)
    )

    for table_name, privileges in role.table_privileges.items():
        connection.execute(
            sql.SQL("REVOKE ALL PRIVILEGES ON TABLE {} FROM {}").format(
                sql.Identifier("public", table_name),
                role_identifier,
            )
        )
        privilege_list = sql.SQL(", ").join(sql.SQL(item) for item in privileges)
        connection.execute(
            sql.SQL("GRANT {} ON TABLE {} TO {}").format(
                privilege_list,
                sql.Identifier("public", table_name),
                role_identifier,
            )
        )


def provision_roles(
    admin_url: str,
    output_directory: Path,
) -> tuple[Path, ...]:
    output_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    output_directory.chmod(0o700)
    written: list[Path] = []

    with psycopg.connect(admin_url, autocommit=True, connect_timeout=8) as connection:
        database_name = connection.info.dbname
        connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")

        for role in ROLES:
            secret_path = output_directory / role.secret_filename
            if secret_path.exists():
                existing_url = secret_path.read_text(encoding="utf-8").strip()
                existing_username = urlsplit(existing_url).username
                if existing_username == role.username:
                    password = _password_from_url(existing_url)
                    reset_password = not _role_exists(connection, role.username)
                else:
                    password = secrets.token_urlsafe(36)
                    reset_password = True
            else:
                password = secrets.token_urlsafe(36)
                reset_password = True

            _ensure_login_role(
                connection,
                role.username,
                password,
                reset_password=reset_password,
            )
            _apply_privileges(connection, role, database_name)

            database_url = database_url_for_user(
                admin_url,
                role.username,
                password,
            )
            secret_path.write_text(database_url, encoding="utf-8")
            secret_path.chmod(0o600)
            written.append(secret_path)
            print(f"Provisioned restricted database role {role.username}.")

    return tuple(written)


def main() -> None:
    admin_secret = Path(
        os.environ.get(
            "DATABASE_ADMIN_URL_FILE",
            "/run/secrets/database-admin-url",
        )
    )
    output_directory = Path(
        os.environ.get("DATABASE_SECRET_OUTPUT", "/run/vesta-secret-output")
    )
    admin_url = admin_secret.read_text(encoding="utf-8").strip()
    provision_roles(admin_url, output_directory)


if __name__ == "__main__":
    main()
