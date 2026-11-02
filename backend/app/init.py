"""One-time start job: run migrations and load first-time data."""

import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.business.models import Clock, DomainError
from app.business.seed_service import SeedService
from app.config import Settings
from app.data_access.database import create_database_engine, create_session_factory
from app.data_access.raw_files import read_raw_data
from app.data_access.unit_of_work import SqlUnitOfWork

ALEMBIC_CONFIG = Path(__file__).resolve().parent.parent / "alembic.ini"

logger = logging.getLogger("hotel.init")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    settings = Settings.from_env()
    command.upgrade(Config(str(ALEMBIC_CONFIG)), "head")

    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)
    service = SeedService(lambda: SqlUnitOfWork(session_factory), Clock())
    try:
        result = service.run(read_raw_data(settings.raw_data_dir))
    except DomainError as error:
        logger.error(error.message)
        return 1
    finally:
        engine.dispose()

    if result.already_completed:
        logger.info("Startdata %s er allerede indlæst. Intet er ændret.", result.version)
    else:
        logger.info(
            "Startdata %s indlæst: %d demobookinger, %d demosalg, %d referenceposter.",
            result.version,
            result.bookings,
            result.bar_sales,
            result.reference_records,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
