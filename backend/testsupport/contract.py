"""Compares real HTTP responses with the versioned OpenAPI contract."""

from functools import lru_cache
from pathlib import Path

import yaml
from openapi_schema_validator import OAS30Validator, oas30_format_checker

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "specs/004-hotelsystem/contracts/openapi.yaml"


@lru_cache
def load_contract() -> dict:
    return yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))


def resolve(node, contract):
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


def assert_matches_contract(response, method: str, path_template: str) -> None:
    """The status must be documented, and the body and headers must follow it."""
    contract = load_contract()
    operation = contract["paths"][path_template][method.lower()]
    status = str(response.status_code)
    assert status in operation["responses"], f"{method} {path_template} has no documented {status}: {response.text}"

    documented = resolve(operation["responses"][status], contract)
    for header in documented.get("headers", {}):
        assert header in response.headers, f"{method} {path_template} {status} is missing header {header}"

    content = documented.get("content")
    if content is None:
        assert response.content == b"", f"{method} {path_template} {status} must not have a body"
        return

    assert response.headers["content-type"].startswith("application/json")
    schema = resolve(content["application/json"]["schema"], contract)
    validator = OAS30Validator(schema, format_checker=oas30_format_checker)
    errors = [f"{list(error.path)}: {error.message}" for error in validator.iter_errors(response.json())]
    assert not errors, f"{method} {path_template} {status}: {errors}"
