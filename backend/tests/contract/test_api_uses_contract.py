"""T004: the running application and Swagger UI must use the versioned contract."""

from pathlib import Path

import pytest
import yaml
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import ROUTERS, create_app
from testsupport.contract import load_contract

REPO_ROOT = Path(__file__).resolve().parents[3]

# Endpoints in the contract that later tasks implement. When one is added, it
# must be removed here, otherwise the test below fails.
NOT_IMPLEMENTED_YET = {
    ("get", "/api/analytics/hotel"),
    ("get", "/api/analytics/bar"),
}


@pytest.fixture()
def app(settings):
    return create_app(settings)


def implemented_operations() -> set[tuple[str, str]]:
    operations = set()
    for router in ROUTERS:
        for route in router.routes:
            assert isinstance(route, APIRoute)
            path = route.path.replace("{booking_id}", "{id}")
            operations.update((method.lower(), path) for method in route.methods)
    assert operations, "The routes must be found, otherwise the checks below prove nothing."
    return operations


def contract_operations() -> set[tuple[str, str]]:
    operations = set()
    for path, item in load_contract()["paths"].items():
        for method in item:
            if method in {"get", "post", "put", "delete", "patch"}:
                operations.add((method, path))
    return operations


def test_every_route_is_in_the_contract():
    assert implemented_operations() - contract_operations() == set()


def test_the_contract_is_implemented_except_for_the_listed_later_tasks():
    assert contract_operations() - implemented_operations() == NOT_IMPLEMENTED_YET


@pytest.mark.parametrize("path", ["/openapi.json", "/docs", "/redoc"])
def test_no_competing_generated_schema_or_docs(app, path):
    assert app.openapi_url is None
    with TestClient(app) as client:
        assert client.get(path).status_code == 404


def test_swagger_ui_shows_the_versioned_contract_read_only():
    compose = yaml.safe_load((REPO_ROOT / "compose.yaml").read_text(encoding="utf-8"))
    swagger = compose["services"]["swagger"]
    assert swagger["environment"]["SWAGGER_JSON"] == "/contract/openapi.yaml"
    assert "./specs/004-hotelsystem/contracts/openapi.yaml:/contract/openapi.yaml:ro" in swagger["volumes"]


def test_only_frontend_and_swagger_are_published_and_only_on_localhost():
    services = yaml.safe_load((REPO_ROOT / "compose.yaml").read_text(encoding="utf-8"))["services"]
    published = {name: service["ports"] for name, service in services.items() if "ports" in service}
    assert published == {"frontend": ["127.0.0.1:8080:80"], "swagger": ["127.0.0.1:8081:8080"]}


def test_startup_order_is_database_then_init_then_backend():
    services = yaml.safe_load((REPO_ROOT / "compose.yaml").read_text(encoding="utf-8"))["services"]
    assert services["init"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert services["backend"]["depends_on"]["init"]["condition"] == "service_completed_successfully"
    assert services["db"]["volumes"] == ["mysql_data:/var/lib/mysql"]
