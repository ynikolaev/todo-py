from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.infra.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for SQLAlchemy models."""

    @declared_attr.directive
    def __table_args__(self):
        return {"schema": settings.TELEGRAM_SCHEMA_NAME}

    pass
