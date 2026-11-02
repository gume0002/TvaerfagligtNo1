"""T004: checks that the versioned OpenAPI document is valid and complete.

This covers the document only. Comparing it with real HTTP responses, and
checking that Swagger UI and the backend use this file, needs the backend and
Compose setup from later tasks.
"""

from pathlib import Path

import pytest
import yaml
from openapi_schema_validator import OAS30Validator
from openapi_spec_validator import validate

CONTRACT_PATH = Path(__file__).resolve().parents[3] / "specs/004-hotelsystem/contracts/openapi.yaml"

# The endpoint table in specs/004-hotelsystem/plan.md, section 5.
PLANNED_OPERATIONS = {
    ("get", "/api/bookings"),
    ("post", "/api/bookings"),
    ("get", "/api/bookings/{id}"),
    ("put", "/api/bookings/{id}"),
    ("delete", "/api/bookings/{id}"),
    ("get", "/api/bar-sales"),
    ("post", "/api/bar-sales"),
    ("get", "/api/bar-sales/{id}"),
    ("put", "/api/bar-sales/{id}"),
    ("delete", "/api/bar-sales/{id}"),
    ("get", "/api/catalogs"),
    ("get", "/api/analytics/hotel"),
    ("get", "/api/analytics/bar"),
    ("get", "/api/health"),
}
# The Tableau feed, added after the Tableau Public test in T002.
FEED_OPERATIONS = {("get", "/api/odata/"), ("get", "/api/odata/$metadata")} | {
    ("get", f"/api/odata/{name}")
    for name in (
        "HotelTotals",
        "HotelRoomTypeSeason",
        "HotelCountries",
        "HotelRoomTypeRanks",
        "BarTotals",
        "BarDrinks",
        "BarCategories",
    )
}
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}


@pytest.fixture(scope="module")
def contract():
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def resolve(node, contract):
    """Inline every local $ref. The document has no recursive schemas."""
    if isinstance(node, dict):
        if "$ref" in node:
            target = contract
            for part in node["$ref"].removeprefix("#/").split("/"):
                target = target[part]
            return resolve(target, contract)
        return {key: resolve(value, contract) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve(item, contract) for item in node]
    return node


def operations(contract):
    for path, item in contract["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS:
                yield method, path, operation


def json_media_types(contract):
    """Yield every JSON body in the document as (location, media type)."""
    for method, path, operation in operations(contract):
        request = resolve(operation.get("requestBody", {}), contract)
        if "content" in request:
            yield f"{method} {path} request", request["content"]["application/json"]
        for status, response in operation["responses"].items():
            content = resolve(response, contract).get("content")
            if content and "application/json" in content:
                yield f"{method} {path} {status}", content["application/json"]


def test_document_is_valid_openapi_3_0(contract):
    assert contract["openapi"] == "3.0.3"
    validate(contract)


def test_document_has_exactly_the_planned_operations(contract):
    actual = {(method, path) for method, path, _ in operations(contract)}
    assert actual == PLANNED_OPERATIONS | FEED_OPERATIONS


def test_operation_ids_are_unique(contract):
    ids = [operation["operationId"] for _, _, operation in operations(contract)]
    assert len(ids) == len(set(ids))


def test_examples_match_their_schemas(contract):
    checked = 0
    for location, media_type in json_media_types(contract):
        if "example" in media_type:
            schema = resolve(media_type["schema"], contract)
            errors = [error.message for error in OAS30Validator(schema).iter_errors(media_type["example"])]
            assert not errors, f"{location}: {errors}"
            checked += 1
    assert checked >= 8


def test_every_error_response_uses_the_shared_error_schema(contract):
    error_schema = resolve({"$ref": "#/components/schemas/Error"}, contract)
    for location, media_type in json_media_types(contract):
        status = location.rsplit(" ", 1)[-1]
        if status.startswith(("4", "5")):
            assert resolve(media_type["schema"], contract) == error_schema, location


@pytest.mark.parametrize("path", ["/api/bookings", "/api/bar-sales"])
def test_create_requires_idempotency_key_and_returns_location(contract, path):
    operation = contract["paths"][path]["post"]
    parameters = resolve(operation["parameters"], contract)
    key = next(item for item in parameters if item["name"] == "Idempotency-Key")
    assert key["in"] == "header" and key["required"] is True
    assert "Location" in operation["responses"]["201"]["headers"]


@pytest.mark.parametrize("path", ["/api/bookings/{id}", "/api/bar-sales/{id}"])
def test_delete_is_a_204_without_a_body(contract, path):
    response = contract["paths"][path]["delete"]["responses"]["204"]
    assert "content" not in response


def test_write_operations_document_their_conflicts(contract):
    for path, method in [
        ("/api/bookings", "post"),
        ("/api/bookings/{id}", "put"),
        ("/api/bar-sales", "post"),
        ("/api/bar-sales/{id}", "put"),
    ]:
        assert "409" in contract["paths"][path][method]["responses"]


def test_satisfaction_can_never_carry_a_score(contract):
    satisfaction = contract["components"]["schemas"]["HotelAnalytics"]["properties"]["satisfaction"]
    assert satisfaction["additionalProperties"] is False
    assert set(satisfaction["properties"]) == {"status"}
    assert satisfaction["properties"]["status"]["enum"] == ["no_data"]
