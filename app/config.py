"""Environment settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    nyc_open_data_app_token: str = ""
    nyc_open_data_base_url: str = "https://data.cityofnewyork.us/resource"
    geoclient_api_key: str = ""
    geoclient_base_url: str = "https://api.nyc.gov/geo/geoclient/v2"

    database_url: str = ""

    llm_api_key: str = ""
    llm_model: str = ""

    smtp_url: str = ""
    sms_api_key: str = ""

    cache_ttl_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
