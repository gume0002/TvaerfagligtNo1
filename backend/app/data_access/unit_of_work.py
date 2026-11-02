"""One database transaction, and translation of MySQL errors to domain errors."""

from sqlalchemy.exc import DBAPIError, InterfaceError
from sqlalchemy.orm import Session, sessionmaker

from app.business.models import RetryableTransactionError, TemporarilyUnavailable
from app.data_access.repositories import (
    SqlBookingRepository,
    SqlCatalogRepository,
    SqlHealthRepository,
    SqlIdempotencyRepository,
    SqlSeedRepository,
)

MYSQL_LOCK_WAIT_TIMEOUT = 1205
MYSQL_DEADLOCK = 1213
# Too many connections, server shutting down, cannot connect, server gone, lost connection.
MYSQL_UNAVAILABLE = {1040, 1053, 2002, 2003, 2006, 2013, 2055}
UNAVAILABLE_MESSAGE = "Systemet er midlertidigt utilgængeligt. Prøv igen."


def _domain_error(error: DBAPIError) -> Exception | None:
    """Translate temporary problems only. A violated constraint is a real bug and must not look temporary."""
    code = error.orig.args[0] if error.orig is not None and error.orig.args else None
    if code in (MYSQL_LOCK_WAIT_TIMEOUT, MYSQL_DEADLOCK):
        return RetryableTransactionError()
    if code in MYSQL_UNAVAILABLE or error.connection_invalidated or isinstance(error, InterfaceError):
        return TemporarilyUnavailable(UNAVAILABLE_MESSAGE)
    return None


class SqlUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def __enter__(self) -> "SqlUnitOfWork":
        self._session = self._session_factory()
        self.catalogs = SqlCatalogRepository(self._session)
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
            # already gone and the transaction has been rolled back by MySQL.
            pass
        if isinstance(exc, DBAPIError):
            translated = _domain_error(exc)
            if translated is not None:
                raise translated from exc

    def commit(self) -> None:
        self._session.commit()
