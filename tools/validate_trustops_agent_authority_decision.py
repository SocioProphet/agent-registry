#!/usr/bin/env python3
"""Validate TrustOps agent authority decision contracts.

This validator is intentionally stdlib-only. It enforces the boundary that a
TrustOps receipt is evidence while an agent authority change is a governed
decision with an effective time and restoration policy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts" / "trustops" / "agent-authority-decision.v0.1.schema.json"
EXAMPLE = ROOT / "contracts" / "trustops" / "agent-authority-decision.v0.1.example.json"
INVALID_PASS_REVOKED = ROOT / "contracts" / "trustops" / "agent-authority-decision.pass-revoked.invalid.json"

REQUIRED_TOP_LEVEL = {
    "schemaVersion",
    "recordType",
    "recordId",
    "agentRef",
    "receiptRef",
    "receipt_outcome",
    "authority_decision",
    "effective_at",
    "decision_timestamp",
    "policyRefs",
    "gateRefs",
    "evidenceRefs",
    "authorityEffects",
    "restored_by_policy",
}

RECEIPT_RANK = {
    "pass": 0,
    "warn": 1,
    "require-review": 2,
    "quarantine": 3,
    "block": 4,
    "rollback": 5,
    "revoke": 6,
}

AUTHORITY_RANK = {
    "unchanged": 0,
    "reduced": 1,
    "suspended": 2,
    "revoked": 3,
}

MAX_AUTHORITY_BY_RECEIPT = {
    "pass": "unchanged",
    "warn": "reduced",
    "require-review": "reduced",
    "quarantine": "suspended",
    "block": "suspended",
    "rollback": "suspended",
    "revoke": "revoked",
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


def require_non_empty_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        fail(f"{key}: expected non-empty string")
    return value


def require_non_empty_list(record: dict[str, Any], key: str) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key}: expected non-empty list")
    return value


def validate_schema(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("schema must use JSON Schema draft 2020-12")
    if schema.get("additionalProperties") is not False:
        fail("schema must be strict")
    required = set(schema.get("required", []))
    missing = sorted(REQUIRED_TOP_LEVEL - required)
    if missing:
        fail(f"schema missing required fields: {missing}")
    props = schema.get("properties", {})
    if props.get("schemaVersion", {}).get("const") != "agent-registry.trustops-agent-authority-decision.v0.1":
        fail("schemaVersion const mismatch")
    if props.get("recordType", {}).get("const") != "TrustOpsAgentAuthorityDecision":
        fail("recordType const mismatch")


def validate_record(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_TOP_LEVEL - set(record))
    if missing:
        fail(f"missing required fields: {missing}")

    if record["schemaVersion"] != "agent-registry.trustops-agent-authority-decision.v0.1":
        fail("schemaVersion mismatch")
    if record["recordType"] != "TrustOpsAgentAuthorityDecision":
        fail("recordType mismatch")

    for key in (
        "recordId",
        "agentRef",
        "receiptRef",
        "receipt_outcome",
        "authority_decision",
        "effective_at",
        "decision_timestamp",
    ):
        require_non_empty_string(record, key)

    for key in ("policyRefs", "gateRefs", "evidenceRefs"):
        values = require_non_empty_list(record, key)
        for index, value in enumerate(values):
            if not isinstance(value, str) or not value:
                fail(f"{key}[{index}]: expected non-empty string")

    receipt_outcome = record["receipt_outcome"]
    authority_decision = record["authority_decision"]
    if receipt_outcome not in RECEIPT_RANK:
        fail(f"unknown receipt_outcome: {receipt_outcome}")
    if authority_decision not in AUTHORITY_RANK:
        fail(f"unknown authority_decision: {authority_decision}")

    max_authority = MAX_AUTHORITY_BY_RECEIPT[receipt_outcome]
    if AUTHORITY_RANK[authority_decision] > AUTHORITY_RANK[max_authority]:
        fail(
            "authority_decision exceeds receipt_outcome bound: "
            f"{receipt_outcome} -> {authority_decision}"
        )

    if receipt_outcome in {"block", "rollback", "revoke"} and authority_decision == "unchanged":
        fail(f"{receipt_outcome} cannot leave authority unchanged")

    effects = record.get("authorityEffects")
    if not isinstance(effects, dict):
        fail("authorityEffects must be an object")
    for key in ("toolAccess", "memoryAccess", "autonomousExecution", "routeEligibility", "egressMode"):
        require_non_empty_string(effects, key)

    restored = record.get("restored_by_policy")
    if not isinstance(restored, dict):
        fail("restored_by_policy must be an object")
    if not isinstance(restored.get("allowed"), bool):
        fail("restored_by_policy.allowed must be boolean")
    require_non_empty_string(restored, "policyRef")
    if restored.get("allowed") is True:
        conditions = restored.get("restoration_conditions")
        if not isinstance(conditions, list) or not conditions:
            fail("restored_by_policy.restoration_conditions required when restoration is allowed")


def main() -> int:
    try:
        validate_schema(load_json(SCHEMA))
        validate_record(load_json(EXAMPLE))
        try:
            validate_record(load_json(INVALID_PASS_REVOKED))
        except ValidationError:
            pass
        else:
            fail("invalid pass->revoked fixture unexpectedly validated")
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("OK: TrustOps agent authority decision contract validates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
