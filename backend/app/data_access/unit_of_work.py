"""One database transaction, and translation of PostgreSQL errors to domain errors."""

from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.business.models import RetryableTransactionError, TemporarilyUnavailable
from app.data_access.repositories import (
    SqlBookingRepository,
    SqlCatalogRepository,
    SqlHealthRepository,
    SqlIdempotencyRepository,
    SqlSeedRepository,
    SqlSaleRepository,
)

# Deadlock, lock timeout and serialization failure. The transaction may be tried again.
POSTGRES_RETRYABLE = {"40P01", "55P03", "40001"}
# Too many connections, shutting down, starting up.
POSTGRES_UNAVAILABLE = {"53300", "57P01", "57P02", "57P03"}
UNAVAILABLE_MESSAGE = "Systemet er midlertidigt utilgængeligt. Prøv igen."


def _domain_error(error: DBAPIError) -> Exception | None:
    """Translate temporary problems only. A violated constraint is a real bug and must not look temporary."""
    code = getattr(error.orig, "sqlstate", None)
    if code in POSTGRES_RETRYABLE:
        return RetryableTransactionError()
    # Connection failures have no SQL state, or one in class 08.
    connection_failed = isinstance(error, OperationalError) and (code is None or code.startswith("08"))
    if code in POSTGRES_UNAVAILABLE or connection_failed or error.connection_invalidated or isinstance(error, InterfaceError):
        return TemporarilyUnavailable(UNAVAILABLE_MESSAGE)
    return None


class SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def __enter__(self) -> "SqlUnitOfWork":
        self._session = self._session_factory()
        self.catalogs = SqlCatalogRepository(self._session)
        self.sales = SqlSaleRepository(self._session)
        self.bookings = SqlBookingRepository(self._session)
        self.idempotency = SqlIdempotencyRepository(self._session)
        self.seed = SqlSeedRepository(self._session)
        self.health = SqlHealthRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        try:
            self._session.rollback()
            self._session.close()
        except DBAPIError:
            # The original error says more. Without one, the connection is
            # already gone and the transaction has been rolled back by PostgreSQL.
            pass
        if isinstance(exc, DBAPIError):
            translated = _domain_error(exc)
            if translated is not None:
                raise translated from exc

    def begin_snapshot(self) -> None:
        # This must be the first operation in an analysis transaction. The
        # snapshot starts at the first read and covers later catalog and relationship reads.
        connection = self._session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")

    def commit(self) -> None:
        self._session.commit()
