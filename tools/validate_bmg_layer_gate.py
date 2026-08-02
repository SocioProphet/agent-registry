#!/usr/bin/env python3
"""Validate BMG-1 layer-gate decision records (SP-ARCH-002 D5).

BMG-1: every agent action is Layer-1 (behavioural, autonomous within the manifest)
or Layer-2 (architectural, mutates the manifest / the set of permissible future
actions). Any action that alters the set of permissible future actions is Layer-2,
and Layer-2 is never autonomous — it requires human sign-off. Validation is
fail-closed: an ambiguous or under-specified record is rejected.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/control-plane/bmg-layer-gate.v0.1.schema.json"
EXAMPLE = ROOT / "contracts/control-plane/bmg-layer-gate.v0.1.example.json"

SCHEMA_VERSION = "agent-registry.bmg-layer-gate.v0.1"
RECORD_TYPE = "BmgLayerGateDecision"

REQUIRED = {
    "schemaVersion",
    "recordType",
    "decisionId",
    "subjectAgent",
    "actionId",
    "layer",
    "effects",
    "autonomy",
    "humanSignoff",
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
        raise ValidationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        fail("expected object")
    return payload


def need_str(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value  # type: ignore[return-value]


def need_bool(record: dict[str, Any], key: str) -> bool:
    value = record.get(key)
    if not isinstance(value, bool):
        fail(f"{key}: expected boolean")
    return value  # type: ignore[return-value]


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    missing = sorted(REQUIRED - set(schema.get("required", [])))
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != SCHEMA_VERSION:
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != RECORD_TYPE:
        fail("recordType const mismatch")


def validate_record(record: dict[str, Any]) -> None:
    """Enforce BMG-1 on a single decision record. Raises ValidationError if invalid."""
    missing = sorted(REQUIRED - set(record))
    if missing:
        fail(f"record missing required fields: {missing}")
    # Fail-closed: mirror the schema's additionalProperties:false. All top-level
    # fields are required, so any key outside REQUIRED is unexpected.
    extra = sorted(set(record) - REQUIRED)
    if extra:
        fail(f"unexpected top-level fields: {extra}")
    if record["schemaVersion"] != SCHEMA_VERSION:
        fail("schemaVersion mismatch")
    if record["recordType"] != RECORD_TYPE:
        fail("recordType mismatch")
    need_str(record, "decisionId")
    if not need_str(record, "subjectAgent").startswith("agent://"):
        fail("subjectAgent must use agent://")
    need_str(record, "actionId")
    need_str(record, "policyRef")

    layer = record.get("layer")
    if layer not in {"behavioural", "architectural"}:
        fail("layer must be 'behavioural' or 'architectural'")

    autonomy = record.get("autonomy")
    if autonomy not in {"autonomous", "human_gated"}:
        fail("autonomy must be 'autonomous' or 'human_gated'")

    effects = record.get("effects")
    if not isinstance(effects, dict):
        fail("effects must be an object")
    extra_effects = sorted(set(effects) - {"mutatesManifest", "altersPermissibleFutureActions"})
    if extra_effects:
        fail(f"unexpected fields in effects: {extra_effects}")
    mutates = need_bool(effects, "mutatesManifest")
    alters = need_bool(effects, "altersPermissibleFutureActions")

    signoff = record.get("humanSignoff")
    if signoff is not None:
        if not isinstance(signoff, dict):
            fail("humanSignoff must be an object or null")
        extra_signoff = sorted(set(signoff) - {"signer", "signedAt", "capabilityDelta"})
        if extra_signoff:
            fail(f"unexpected fields in humanSignoff: {extra_signoff}")
        need_str(signoff, "signer")
        need_str(signoff, "signedAt")
        need_str(signoff, "capabilityDelta")

    # --- BMG-1 core invariant ---
    # Any action that alters the set of permissible future actions (or mutates the
    # manifest) is architectural (Layer-2). This is the load-bearing rule.
    if (alters or mutates) and layer != "architectural":
        fail(
            "BMG-1 violated: an action that mutates the manifest or alters the set "
            "of permissible future actions must be classified 'architectural' (Layer-2)"
        )

    if layer == "architectural":
        # Layer-2 is never autonomous and always carries human sign-off.
        if autonomy != "human_gated":
            fail("BMG-1 violated: architectural (Layer-2) actions must be human_gated")
        if signoff is None:
            fail("BMG-1 violated: architectural (Layer-2) actions require humanSignoff")
    else:  # behavioural / Layer-1
        # Layer-1 stays strictly inside the manifest.
        if mutates or alters:
            fail("behavioural (Layer-1) actions must not mutate the manifest or alter future actions")


def validate_example(example: dict[str, Any]) -> None:
    validate_record(example)


def main() -> int:
    try:
        validate_schema(load(SCHEMA))
        validate_example(load(EXAMPLE))
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: BmgLayerGateDecision validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
