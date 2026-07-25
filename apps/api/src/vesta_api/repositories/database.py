from sqlalchemy import Engine, create_engine


def sqlalchemy_database_url(database_url: str) -> str:
    """Return a SQLAlchemy psycopg URL for common PostgreSQL URI variants."""
    if database_url.startswith("postgres://"):
        return f"postgresql+psycopg://{database_url.removeprefix('postgres://')}"
    if database_url.startswith("postgresql://"):
        return (
            f"postgresql+psycopg://"
            f"{database_url.removeprefix('postgresql://')}"
        )
    return database_url


def create_database_engine(database_url: str) -> Engine:
    return create_engine(
        sqlalchemy_database_url(database_url),
        connect_args={
            "connect_timeout": 5,
            # Exoscale exposes a pgBouncer endpoint. Disabling client-side
            # prepared statements keeps the connection safe in transaction
            # pooling mode.
            "prepare_threshold": None,
        },
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,
        max_overflow=5,
    )
