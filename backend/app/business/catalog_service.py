"""Read access to the catalogs."""

from app.business.models import Catalogs
from app.business.ports import UnitOfWorkFactory


class CatalogService:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def get_catalogs(self) -> Catalogs:
        with self._uow_factory() as uow:
            return uow.catalogs.get_all()
