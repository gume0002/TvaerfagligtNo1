"""T010: the three layers may only depend on what the architecture allows."""

import ast
import re
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[2] / "app"

# Layer rules. data_access may use the domain objects, because the business
# layer's interface returns those, but it never calls a service.
FORBIDDEN_IMPORTS = {
    "api": ("app.data_access", "sqlalchemy", "pymysql", "alembic", "openpyxl"),
    "business": ("app.api", "app.data_access", "app.config", "app.main", "sqlalchemy", "pymysql", "alembic", "fastapi", "starlette", "pydantic", "openpyxl"),
    "data_access": ("app.api", "app.main", "fastapi", "starlette"),
}
ALLOWED_FROM_BUSINESS_IN_DATA_ACCESS = {"app.business.models"}
SQL_PATTERN = re.compile(
    r"\b(SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|TRUNCATE\s+TABLE|FOR\s+UPDATE)\b",
    re.IGNORECASE | re.DOTALL,
)


def imported_modules(source: str) -> set[str]:
    modules = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def layer_violations(layer: str, source: str) -> list[str]:
    violations = []
    for module in imported_modules(source):
        for forbidden in FORBIDDEN_IMPORTS[layer]:
            if module == forbidden or module.startswith(forbidden + "."):
                violations.append(f"imports {module}")
        if layer == "data_access" and module.startswith("app.business") and module not in ALLOWED_FROM_BUSINESS_IN_DATA_ACCESS:
            violations.append(f"imports {module}")
    if layer != "data_access":
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and SQL_PATTERN.search(node.value):
                violations.append(f"contains SQL: {node.value[:40]}")
    return violations


@pytest.mark.parametrize("layer", list(FORBIDDEN_IMPORTS))
def test_layer_follows_the_architecture(layer):
    files = list((APP_DIR / layer).glob("*.py"))
    assert files
    for path in files:
        assert layer_violations(layer, path.read_text(encoding="utf-8")) == [], path.name


@pytest.mark.parametrize(
    ("layer", "source"),
    [
        ("api", "from app.data_access.repositories import SqlBookingRepository"),
        ("api", "import sqlalchemy"),
        ("api", "query = 'SELECT id FROM bookings'"),
        ("business", "from app.data_access.unit_of_work import SqlUnitOfWork"),
        ("business", "from fastapi import FastAPI"),
        ("business", "from sqlalchemy import select"),
        ("business", "query = 'select * for update'"),
        ("data_access", "from app.business.booking_service import BookingService"),
        ("data_access", "from app.api.schemas import money"),
    ],
)
def test_the_check_catches_shortcuts(layer, source):
    assert layer_violations(layer, source)


def test_allowed_dependencies_are_not_flagged():
    assert layer_violations("api", "from app.business.booking_service import BookingService") == []
    assert layer_violations("data_access", "from app.business.models import Booking") == []
