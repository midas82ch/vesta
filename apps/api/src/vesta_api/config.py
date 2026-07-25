from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "seed" / "offers.example.json"
)
DEFAULT_SOURCE_CATALOG_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "sources" / "bern_offers.json"
)
DEFAULT_DIALOGUE_CATALOG_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "seed" / "dialogue_catalog.json"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development", validation_alias="VESTA_ENV")
    database_url: SecretStr | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )
    database_url_file: Path | None = Field(
        default=None,
        validation_alias="DATABASE_URL_FILE",
    )
    offer_data_path: Path = DEFAULT_DATA_PATH
    offer_source_catalog_path: Path = Field(
        default=DEFAULT_SOURCE_CATALOG_PATH,
        validation_alias="OFFER_SOURCE_CATALOG_PATH",
    )
    dialogue_catalog_path: Path = Field(
        default=DEFAULT_DIALOGUE_CATALOG_PATH,
        validation_alias="DIALOGUE_CATALOG_PATH",
    )
    ai_enabled: bool = Field(default=False, validation_alias="VESTA_AI_ENABLED")
    ai_provider: str = Field(default="anthropic", validation_alias="VESTA_AI_PROVIDER")
    ai_model: str = Field(default="claude-haiku-4-5", validation_alias="VESTA_AI_MODEL")
    anthropic_api_key: SecretStr | None = Field(
        default=None, validation_alias="ANTHROPIC_API_KEY"
    )
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="VESTA_OPENAI_MODEL")
    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    def get_database_url(self) -> str | None:
        if self.database_url_file is not None:
            database_url = self.database_url_file.read_text(encoding="utf-8").strip()
            if not database_url:
                raise RuntimeError("DATABASE_URL_FILE is empty")
        elif self.database_url is not None:
            database_url = self.database_url.get_secret_value()
        else:
            return None

        if self.environment.lower() == "production":
            sslmode = parse_qs(urlsplit(database_url).query).get("sslmode", [])
            if not sslmode or sslmode[-1] not in {"require", "verify-ca", "verify-full"}:
                raise RuntimeError(
                    "Production DATABASE_URL must use sslmode=require or stronger"
                )
        return database_url


settings = Settings()
