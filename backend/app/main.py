"""Application start: connects the three layers and has no logic of its own."""

from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import bookings, catalogs, health, sales
from app.api.errors import register_error_handlers
from app.business.sale_service import SaleService
from app.business.booking_service import BookingService
from app.business.catalog_service import CatalogService
from app.business.health_service import HealthService
from app.business.models import Clock
from app.config import Settings
from app.data_access.database import create_database_engine, create_session_factory
from app.data_access.unit_of_work import SqlUnitOfWork


ROUTERS = (bookings.router, catalogs.router, health.router, sales.router)


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    clock = clock or Clock()

    # The contract in specs/004-hotelsystem/contracts/openapi.yaml is the only
    # API description, so FastAPI's generated schema and docs are turned off.
    app = FastAPI(title="Hotel Kong Arthur API", openapi_url=None, docs_url=None, redoc_url=None)

    session_factory = create_session_factory(create_database_engine(settings))
    uow_factory = lambda: SqlUnitOfWork(session_factory)  # noqa: E731
    app.state.sale_service = SaleService(uow_factory, clock)
    app.state.booking_service = BookingService(uow_factory, clock)
    app.state.catalog_service = CatalogService(uow_factory)
    app.state.health_service = HealthService(uow_factory)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        return await call_next(request)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Content-Type", "Idempotency-Key"],
            expose_headers=["Location", "Retry-After"],
        )

    register_error_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    return app
