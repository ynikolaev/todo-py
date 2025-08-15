import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings

REFRESH_FILE = os.environ.get(
    "SERVICE_REFRESH_TOKEN_FILE", "/shared/service_refresh.token"
)


class ServiceConfig(BaseSettings):
    # General
    APP_ENV: str = "dummy"
    LOG_LEVEL: str = "dummy"

    # Django settings
    DJANGO_SUPERUSER_USERNAME: str = "dummy"
    DJANGO_SUPERUSER_EMAIL: str = "dummy@example.com"
    DJANGO_SUPERUSER_PASSWORD: SecretStr | None = None
    DJANGO_SECRET_KEY: SecretStr = SecretStr("dummy_secret")
    DJANGO_DEBUG: bool = False
    DJANGO_ALLOWED_HOSTS: str = "dummy"

    # Redis
    REDIS_HOST: str = "dummy"
    REDIS_PORT: int = 6379

    # PostgreSQL
    POSTGRES_HOST: str = "dummy"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dummy"
    POSTGRES_USER: str = "dummy"
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_READ_WRITE_USER: str = "dummy"
    POSTGRES_READ_WRITE_PASSWORD: SecretStr | None = None

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: SecretStr = SecretStr("dummy")
    TELEGRAM_DB_NAME: str = "dummy"
    TELEGRAM_BOT_SHARED_SECRET: SecretStr = SecretStr("dummy")
    TELEGRAM_BOT_SERVICE_USERNAME: str = "dummy"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

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

    class Config:
        env_prefix = ""
        case_sensitive = True


service_config = ServiceConfig()
