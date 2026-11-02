"""Decides whether the system is ready to serve requests."""

from app.business.models import TemporarilyUnavailable
from app.business.ports import UnitOfWorkFactory


class HealthService:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def check_ready(self) -> None:
        with self._uow_factory() as uow:
            uow.health.ping()
            if not uow.seed.any_completed():
                raise TemporarilyUnavailable("Systemet er ved at starte. Prøv igen.")
