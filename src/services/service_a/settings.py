"""Service A settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service A settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    app_name: str = ""
    service_b_url: str = ""
    debug: bool = False


settings = Settings()  # type: ignore[call-arg]


def get_settings() -> Settings:
    """Get application settings."""
    return settings
