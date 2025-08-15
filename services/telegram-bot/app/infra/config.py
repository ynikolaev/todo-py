import os

from pydantic import AnyUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REFRESH_FILE = os.environ.get(
    "SERVICE_REFRESH_TOKEN_FILE", "/shared/service_refresh.token"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    # Bot settings
    TELEGRAM_BOT_TOKEN: SecretStr | None = None
    TELEGRAM_BOT_SHARED_SECRET: SecretStr = SecretStr("dummy_secret")
    TELEGRAM_BOT_SERVICE_USERNAME: str = "dummy_bot_service"
    TELEGRAM_BOT_SERVICE_PASSWORD: SecretStr = SecretStr("dummy_password")

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Django settings
    DJANGO_API_BASE: AnyUrl = AnyUrl("http://crud-django-service:8000")

    # PostgreSQL settings
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

    @property
    def SERVICE_REFRESH_TOKEN(self) -> str:  # noqa: N802
        with open(REFRESH_FILE) as f:
            result = f.read().strip()
            import base64
            import json

            h, p, _ = result.split(".")
            payload = json.loads(base64.urlsafe_b64decode(p + "=="))
            print("token_type:", payload.get("token_type"), "exp:", payload.get("exp"))
        return result


settings = Settings()
