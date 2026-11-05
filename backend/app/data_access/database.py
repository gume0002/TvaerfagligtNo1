"""PostgreSQL connection setup."""

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings


def create_database_engine(settings: Settings) -> Engine:
    url = URL.create(
        "postgresql+psycopg",
        username=settings.database_user,
        password=settings.database_password,
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
    )
    return create_engine(
        url,
        isolation_level="READ COMMITTED",
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={"connect_timeout": 5, "options": "-c lock_timeout=30s"},
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False, autoflush=False)
