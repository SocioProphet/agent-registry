#!/usr/bin/env python3
"""Validate WallGuard agent wall-context registry contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "wallguard" / "agent-wall-context.v0.1.schema.json"
VALID = ROOT / "contracts" / "wallguard" / "agent-wall-context.active.example.json"
REVOKED_INVALID = ROOT / "contracts" / "wallguard" / "agent-wall-context.revoked-invalid.json"
CONTAMINATED_INVALID = ROOT / "contracts" / "wallguard" / "agent-wall-context.contaminated-global-invalid.json"

REQUIRED = {
    "schemaVersion",
    "recordType",
    "contextId",
    "agentRef",
    "sessionRef",
    "activeWorkroomRef",
    "clientRef",
    "matterRef",
    "wallRef",
    "memberships",
    "recusalState",
    "sessionState",
    "allowedMemoryCompartments",
    "allowedToolClasses",
    "evidenceRefs",
    "receipt_hash",
}

class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        fail(f"{path.relative_to(ROOT)}: expected JSON object")
    return payload


def require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def require_list(record: dict[str, Any], key: str) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key}: expected non-empty list")
    return value


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing required fields: {missing}")


def validate_context(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"wall context missing required fields: {missing}")
    if record["schemaVersion"] != "agent-registry.agent-wall-context.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "AgentWallContext":
        fail("recordType mismatch")
    for key in ("contextId", "agentRef", "sessionRef", "activeWorkroomRef", "clientRef", "matterRef", "wallRef"):
        require_string(record, key)
    if not require_string(record, "receipt_hash").startswith("sha256:"):
        fail("receipt_hash must be sha256-bound")
    require_list(record, "evidenceRefs")
    memberships = require_list(record, "memberships")

    active_memberships = []
    for index, membership in enumerate(memberships):
        if not isinstance(membership, dict):
            fail(f"memberships[{index}] must be an object")
        for key in ("wallRef", "clientRef", "matterRef", "status", "scope", "acknowledgmentRef"):
            require_string(membership, key)
        if membership["wallRef"] == record["wallRef"] and membership["clientRef"] == record["clientRef"] and membership["matterRef"] == record["matterRef"]:
            if membership["status"] == "active":
                active_memberships.append(membership)

    if record["recusalState"] != "none":
        fail("active wall context requires non-recused agent")
    if not active_memberships:
        fail("active wall context requires at least one active matching membership")
    if record["sessionState"] in {"contaminated", "unknown"}:
        compartments = set(record.get("allowedMemoryCompartments", []))
        if compartments & {"global", "firm_approved"}:
            fail("contaminated or unknown sessions must not allow global or firm-approved memory compartments")
    if record["sessionState"] == "wall_scoped" and "wall_restricted" not in set(record.get("allowedMemoryCompartments", [])):
        fail("wall-scoped sessions should include wall_restricted memory compartment")


def expect_invalid(path: Path, validator: Callable[[dict[str, Any]], None], label: str) -> None:
    try:
        validator(load_json(path))
    except ValidationError:
        return
    fail(f"invalid fixture unexpectedly validated: {label}")


def main() -> int:
    try:
        validate_schema(load_json(SCHEMA))
        validate_context(load_json(VALID))
        expect_invalid(REVOKED_INVALID, validate_context, "revoked membership")
        expect_invalid(CONTAMINATED_INVALID, validate_context, "contaminated global memory")
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: agent wall-context contracts validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
