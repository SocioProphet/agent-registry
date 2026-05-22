#!/usr/bin/env python3
"""Validate authority current-state and restoration contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
STATE_SCHEMA = ROOT / "contracts" / "trustops" / "agent-authority-current-state.v0.1.schema.json"
RESTORE_SCHEMA = ROOT / "contracts" / "trustops" / "authority-restoration-decision.v0.1.schema.json"
ACTIVE = ROOT / "contracts" / "trustops" / "agent-authority-current-state.active.example.json"
REDUCED = ROOT / "contracts" / "trustops" / "agent-authority-current-state.reduced.example.json"
SUSPENDED = ROOT / "contracts" / "trustops" / "agent-authority-current-state.suspended.example.json"
REVOKED = ROOT / "contracts" / "trustops" / "agent-authority-current-state.revoked.example.json"
RAW_RECEIPT_INVALID = ROOT / "contracts" / "trustops" / "agent-authority-current-state.raw-receipt.invalid.json"
RESTORE = ROOT / "contracts" / "trustops" / "authority-restoration-decision.restore.example.json"
INVALID_RESTORE = ROOT / "contracts" / "trustops" / "authority-restoration-decision.missing-authorization.invalid.json"

STATE_REQUIRED = {
    "schemaVersion",
    "recordType",
    "stateId",
    "agentRef",
    "computed_at",
    "authority_status",
    "effective_decision_ref",
    "source_decision_refs",
    "evidenceRefs",
    "authorityEffects",
    "restoration_required",
    "receipt_hash",
}

RESTORE_REQUIRED = {
    "schemaVersion",
    "recordType",
    "restorationId",
    "agentRef",
    "prior_state_ref",
    "restoration_decision",
    "decision_actor_ref",
    "decision_actor_kind",
    "authorization_policy_ref",
    "authorization_evidence_refs",
    "restored_authority_status",
    "restored_effects",
    "effective_at",
    "decision_timestamp",
    "receipt_hash",
}

STATUS = {"active", "reduced", "suspended", "revoked"}
RESTORE_DECISIONS = {"restore", "deny", "require-review"}
ACTOR_KINDS = {"human", "policy-engine", "service", "governance-agent"}
EFFECT_FIELDS = ("toolAccess", "memoryAccess", "autonomousExecution", "routeEligibility", "egressMode")


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
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item:
            fail(f"{key}[{index}]: expected non-empty string")
    return value


def require_hash(record: dict[str, Any], key: str) -> None:
    value = require_string(record, key)
    if not value.startswith("sha256:"):
        fail(f"{key} must be sha256-bound")


def validate_schema(schema: dict[str, Any], required: set[str], label: str) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail(f"{label} schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail(f"{label} schema must be strict")
    missing = sorted(required - set(schema.get("required", [])))
    if missing:
        fail(f"{label} schema missing required fields: {missing}")


def validate_effects(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    for key in EFFECT_FIELDS:
        require_string(value, key)


def require_authority_decision_ref(value: str, label: str) -> None:
    if value.startswith("trustops-receipt:"):
        fail(f"{label} must reference an authority decision, not a raw TrustOps receipt")
    if not (
        value.startswith("trustops-agent-authority-decision:")
        or value.startswith("authority-restoration-decision:")
    ):
        fail(f"{label} must reference an authority decision or restoration decision")


def validate_state(record: dict[str, Any]) -> None:
    missing = sorted(STATE_REQUIRED - set(record))
    if missing:
        fail(f"authority current state missing required fields: {missing}")
    if record["schemaVersion"] != "agent-registry.agent-authority-current-state.v0.1":
        fail("state schemaVersion mismatch")
    if record["recordType"] != "AgentAuthorityCurrentState":
        fail("state recordType mismatch")
    for key in ("stateId", "agentRef", "computed_at", "authority_status", "effective_decision_ref"):
        require_string(record, key)
    if record["authority_status"] not in STATUS:
        fail(f"unknown authority_status: {record['authority_status']}")
    require_authority_decision_ref(record["effective_decision_ref"], "effective_decision_ref")
    source_refs = require_list(record, "source_decision_refs")
    for index, source_ref in enumerate(source_refs):
        require_authority_decision_ref(source_ref, f"source_decision_refs[{index}]")
    require_list(record, "evidenceRefs")
    validate_effects(record.get("authorityEffects"), "authorityEffects")
    if not isinstance(record.get("restoration_required"), bool):
        fail("restoration_required must be boolean")
    require_hash(record, "receipt_hash")

    if record["authority_status"] in {"suspended", "revoked"}:
        if record.get("restoration_required") is not True:
            fail("suspended/revoked states require restoration_required=true")
        require_string(record, "restoration_policy_ref")
        require_list(record, "restoration_conditions")

    if record["authority_status"] == "active" and record.get("restoration_required") is not False:
        fail("active state must not require restoration")


def validate_restoration(record: dict[str, Any]) -> None:
    missing = sorted(RESTORE_REQUIRED - set(record))
    if missing:
        fail(f"authority restoration decision missing required fields: {missing}")
    if record["schemaVersion"] != "agent-registry.authority-restoration-decision.v0.1":
        fail("restoration schemaVersion mismatch")
    if record["recordType"] != "AuthorityRestorationDecision":
        fail("restoration recordType mismatch")
    for key in (
        "restorationId",
        "agentRef",
        "prior_state_ref",
        "restoration_decision",
        "decision_actor_ref",
        "decision_actor_kind",
        "authorization_policy_ref",
        "restored_authority_status",
        "effective_at",
        "decision_timestamp",
    ):
        require_string(record, key)
    if record["restoration_decision"] not in RESTORE_DECISIONS:
        fail(f"unknown restoration_decision: {record['restoration_decision']}")
    if record["decision_actor_kind"] not in ACTOR_KINDS:
        fail(f"unknown decision_actor_kind: {record['decision_actor_kind']}")
    if record["restored_authority_status"] not in STATUS:
        fail(f"unknown restored_authority_status: {record['restored_authority_status']}")
    require_list(record, "authorization_evidence_refs")
    validate_effects(record.get("restored_effects"), "restored_effects")
    require_hash(record, "receipt_hash")

    if record["restoration_decision"] == "restore" and record["restored_authority_status"] not in {"active", "reduced"}:
        fail("restore decision must restore to active or reduced")
    if record["restoration_decision"] != "restore" and record["restored_authority_status"] == "active":
        fail("non-restore decisions cannot restore active authority")


def expect_invalid(path: Path, validator: Callable[[dict[str, Any]], None], label: str) -> None:
    try:
        validator(load_json(path))
    except ValidationError:
        return
    fail(f"invalid fixture unexpectedly validated: {label}")


def main() -> int:
    try:
        validate_schema(load_json(STATE_SCHEMA), STATE_REQUIRED, "state")
        validate_schema(load_json(RESTORE_SCHEMA), RESTORE_REQUIRED, "restoration")
        for fixture in (ACTIVE, REDUCED, SUSPENDED, REVOKED):
            validate_state(load_json(fixture))
        validate_restoration(load_json(RESTORE))
        expect_invalid(INVALID_RESTORE, validate_restoration, "missing restoration authorization")
        expect_invalid(RAW_RECEIPT_INVALID, validate_state, "raw receipt derived state")
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: authority state contracts validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
