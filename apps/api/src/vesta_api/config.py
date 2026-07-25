from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATA_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "seed" / "offers.example.json"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development", validation_alias="VESTA_ENV")
    offer_data_path: Path = DEFAULT_DATA_PATH


settings = Settings()
