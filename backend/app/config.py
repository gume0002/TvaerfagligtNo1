"""Backend configuration from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str
    raw_data_dir: Path
    cors_origins: tuple[str, ...]

    @classmethod
    def from_env(cls):
        origins = os.environ.get("CORS_ORIGINS", "")
        return cls(
            database_host=os.environ["DATABASE_HOST"],
            database_port=int(os.environ.get("DATABASE_PORT", "5432")),
            database_name=os.environ["DATABASE_NAME"],
            database_user=os.environ["DATABASE_USER"],
            database_password=os.environ["DATABASE_PASSWORD"],
            raw_data_dir=Path(os.environ.get("RAW_DATA_DIR", "/data/raw")),
            cors_origins=tuple(item.strip() for item in origins.split(",") if item.strip()),
        )
