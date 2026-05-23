#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/control-plane/control-plane-capability-grant.v0.1.schema.json"
EXAMPLE = ROOT / "contracts/control-plane/control-plane-capability-grant.v0.1.example.json"
REQUIRED = {
    "schemaVersion",
    "recordType",
    "grantId",
    "subjectAgent",
    "authorityClass",
    "allowedScopes",
    "deniedScopes",
    "runtimeAuthority",
    "policyRef",
}


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        fail("expected object")
    return payload


def need_str(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def need_list(record: dict[str, Any], key: str, *, non_empty: bool = False) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list):
        fail(f"{key}: expected list")
    if non_empty and not value:
        fail(f"{key}: expected non-empty list")
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            fail(f"{key}[{index}]: expected non-empty string")
    return value


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agent-registry.control-plane-capability-grant.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "ControlPlaneCapabilityGrant":
        fail("recordType const mismatch")


def validate_example(example: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(example))
    if missing:
        fail(f"example missing required fields: {missing}")
    if example["schemaVersion"] != "agent-registry.control-plane-capability-grant.v0.1":
        fail("schemaVersion mismatch")
    if example["recordType"] != "ControlPlaneCapabilityGrant":
        fail("recordType mismatch")
    if not need_str(example, "subjectAgent").startswith("agent://"):
        fail("subjectAgent must use agent://")
    if example["authorityClass"] not in {"tool_grant", "event_read", "event_write", "context_read", "bridge_export"}:
        fail("invalid authorityClass")
    allowed = set(need_list(example, "allowedScopes", non_empty=True))
    denied = set(need_list(example, "deniedScopes"))
    if allowed & denied:
        fail("allowedScopes and deniedScopes overlap")
    need_str(example, "policyRef")
    runtime = example.get("runtimeAuthority")
    if not isinstance(runtime, dict):
        fail("runtimeAuthority must be object")
    state = need_str(runtime, "state")
    if state not in {"active", "reduced", "suspended", "revoked"}:
        fail("invalid runtimeAuthority.state")
    if not isinstance(runtime.get("revoked"), bool):
        fail("runtimeAuthority.revoked must be boolean")
    if state == "revoked" and runtime.get("revoked") is not True:
        fail("revoked state requires revoked=true")
    if runtime.get("revoked") is True and not runtime.get("revocationReason"):
        fail("revoked grant requires revocationReason")
    need_str(runtime, "expiresAt")


def main() -> int:
    try:
        validate_schema(load(SCHEMA))
        validate_example(load(EXAMPLE))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: ControlPlaneCapabilityGrant validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
