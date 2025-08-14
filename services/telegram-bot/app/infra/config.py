from pydantic import AnyUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    TELEGRAM_BOT_TOKEN: SecretStr | None = None
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: SecretStr = SecretStr("app_password")
    POSTGRES_HOST: str = "postgres-db"
    POSTGRES_PORT: int = 5432
    TELEGRAM_SCHEMA_NAME: str = "app_db"
    POSTGRES_DB: str = "app_db"

    @property
    def DATABASE_URL(self) -> AnyUrl:  # noqa: N802
        return AnyUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    WEBHOOK_HOST: str | None = None
    WEBHOOK_PATH: str = "/tg/webhook"
    WEBHOOK_SECRET_TOKEN: SecretStr | None = None


settings = Settings()
