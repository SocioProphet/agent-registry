#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/workspace-context/workspace-context-authority-binding.v0.1.schema.json"
EXAMPLE = ROOT / "contracts/workspace-context/workspace-context-authority-binding.v0.1.example.json"

REQUIRED = {
    "schemaVersion",
    "recordType",
    "bindingId",
    "createdAt",
    "workroomRef",
    "contextGraphRef",
    "runtimeBindingRef",
    "agentRefs",
    "sessionRefs",
    "authorityStateRefs",
    "grantRefs",
    "policyRefs",
    "evidenceRefs",
    "status",
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


def need_list(record: dict[str, Any], key: str) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list) or not value:
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
    if props.get("schemaVersion", {}).get("const") != "agent-registry.workspace-context-authority-binding.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "WorkspaceContextAuthorityBinding":
        fail("recordType const mismatch")


def validate_example(example: dict[str, Any]) -> None:
    missing = sorted(REQUIRED - set(example))
    if missing:
        fail(f"example missing required fields: {missing}")
    if example["schemaVersion"] != "agent-registry.workspace-context-authority-binding.v0.1":
        fail("schemaVersion mismatch")
    if example["recordType"] != "WorkspaceContextAuthorityBinding":
        fail("recordType mismatch")
    if not need_str(example, "workroomRef").startswith("workroom://"):
        fail("workroomRef must use workroom://")
    if example.get("professionalWorkroomRef") is not None and not str(example["professionalWorkroomRef"]).startswith("professional-workroom://"):
        fail("professionalWorkroomRef must use professional-workroom:// when present")
    need_str(example, "contextGraphRef")
    need_str(example, "runtimeBindingRef")
    for key in ("agentRefs", "sessionRefs", "authorityStateRefs", "grantRefs", "policyRefs", "evidenceRefs"):
        need_list(example, key)
    if not isinstance(example.get("revocationRefs", []), list):
        fail("revocationRefs must be list when present")
    if example["status"] not in {"active", "reduced", "suspended", "revoked", "review"}:
        fail("invalid status")


def main() -> int:
    try:
        validate_schema(load(SCHEMA))
        validate_example(load(EXAMPLE))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: WorkspaceContextAuthorityBinding validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
