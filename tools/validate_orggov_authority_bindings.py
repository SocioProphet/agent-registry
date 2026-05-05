#!/usr/bin/env python3
"""Validate OrgGov actor authority binding contracts.

The validator intentionally uses only the Python standard library. It checks the
schema/example pair and cross-reference invariants that make Agent Registry a
usable authority ledger for OrgGov v0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/orggov/actor-authority-binding.v0.1.schema.json"
EXAMPLE = ROOT / "contracts/orggov/actor-authority-binding.v0.1.example.json"


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_matches(value: Any, expected: str) -> bool:
    actual = json_type_name(value)
    if expected == "number":
        return actual in {"integer", "number"}
    return actual == expected


def validate_schema(schema: dict[str, Any], value: Any, path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        fail(f"{path}: expected const {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        fail(f"{path}: {value!r} not in enum {schema['enum']!r}")

    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(value, item) for item in expected_types):
            fail(f"{path}: expected type {expected_types!r}, got {json_type_name(value)!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                fail(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                fail(f"{path}: unexpected properties {extra!r}")

        additional = schema.get("additionalProperties")
        for key, item in value.items():
            child_schema = properties.get(key)
            if child_schema is None and isinstance(additional, dict):
                child_schema = additional
            if child_schema is not None:
                validate_schema(child_schema, item, f"{path}.{key}")

    if isinstance(value, list):
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                validate_schema(item_schema, item, f"{path}[{index}]")


def collect(record: dict[str, Any], key: str, id_key: str) -> set[str]:
    values = record.get(key)
    if not isinstance(values, list) or not values:
        fail(f"{key}: expected non-empty list")
    ids: set[str] = set()
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            fail(f"{key}[{index}]: expected object")
        identifier = item.get(id_key)
        if not isinstance(identifier, str) or not identifier:
            fail(f"{key}[{index}]: missing {id_key}")
        ids.add(identifier)
    return ids


def require_ref(ref: str, known: set[str], label: str) -> None:
    if ref not in known:
        fail(f"{label}: unknown ref {ref!r}")


def require_refs(refs: list[str], known: set[str], label: str) -> None:
    if not isinstance(refs, list):
        fail(f"{label}: expected list")
    for ref in refs:
        require_ref(ref, known, label)


def validate_binding_invariants(record: dict[str, Any]) -> None:
    actor_ids = collect(record, "actors", "actorId")
    role_ids = collect(record, "roles", "roleId")
    authority_ids = collect(record, "authorities", "authorityId")
    grant_ids = collect(record, "capabilityGrants", "grantId")

    local_scope_refs = {record["workroomRef"], record["workOrderRef"]}
    local_asset_action_refs: set[str] = set()
    for authority in record["authorities"]:
        require_refs(authority["allowedActionRefs"], set(authority["allowedActionRefs"]), f"{authority['authorityId']}.allowedActionRefs")
        local_asset_action_refs.update(authority["allowedActionRefs"])
        local_asset_action_refs.update(authority["assetScopeRefs"])

    for role in record["roles"]:
        require_refs(role["authorityRefs"], authority_ids, f"{role['roleId']}.authorityRefs")

    for binding in record["roleBindings"]:
        require_ref(binding["actorRef"], actor_ids, f"{binding['bindingId']}.actorRef")
        require_ref(binding["roleRef"], role_ids, f"{binding['bindingId']}.roleRef")
        require_refs(binding["capabilityGrantRefs"], grant_ids, f"{binding['bindingId']}.capabilityGrantRefs")
        for scope in binding["scopeRefs"]:
            if scope not in local_scope_refs and scope not in local_asset_action_refs:
                fail(f"{binding['bindingId']}.scopeRefs: unexpected scope {scope!r}")
        if binding["status"] == "active" and not binding["policyRefs"]:
            fail(f"{binding['bindingId']}: active binding requires policyRefs")

    active_grants = [grant for grant in record["capabilityGrants"] if grant["status"] == "active"]
    if not active_grants:
        fail("expected at least one active capability grant")

    if record["revocation"].get("supported") is not True:
        fail("revocation.supported must be true")
    if record["revocation"].get("revocationEvidenceRequired") is not True:
        fail("revocation evidence must be required")


def main() -> int:
    try:
        schema = load_json(SCHEMA)
        example = load_json(EXAMPLE)
        validate_schema(schema, example)
        validate_binding_invariants(example)
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2

    print("ok: contracts/orggov/actor-authority-binding.v0.1.example.json validates")
    print("OK: OrgGov actor authority binding validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
