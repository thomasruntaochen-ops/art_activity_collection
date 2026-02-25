from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "art-activity-collection"
    app_env: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "art_activity_collection"

    log_level: str = "INFO"

    llm_enabled: bool = False
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )

    @property
    def mysql_host_resolved(self) -> str:
        host = (self.mysql_host or "").strip()
        if host.lower() in {"localhost", "::1", "[::1]"}:
            return "127.0.0.1"
        return host

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host_resolved}:{self.mysql_port}/{self.mysql_db}"
        )


settings = Settings()
