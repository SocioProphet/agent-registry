#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "trust-chain-agent-manifest-binding.v0.1.schema.json"
PREVIEW_FIXTURE = ROOT / "examples" / "trust-chain-agent-manifest-binding.preview.example.json"
BLOCKED_FIXTURE = ROOT / "examples" / "trust-chain-agent-manifest-binding.blocked.json"

REQUIRED_TRUST_CHAIN_REFS = {
    "runtime_admission_ref",
    "model_admission_ref",
    "tool_admission_ref",
    "policy_profile_ref",
    "guardrail_decision_ref",
    "agentplane_validation_ref",
}


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


def validate_common(record: dict[str, Any], path: Path) -> None:
    agent = record.get("agent", {})
    if not str(agent.get("agent_ref", "")).startswith("agent-registry://"):
        fail(f"{path}: agent_ref must be agent-registry://")
    allowed = record.get("allowed_surfaces", {})
    for field in ("tool_refs", "model_route_refs", "dataset_refs", "memory_scope_refs", "runtime_class_refs"):
        if field not in allowed or not isinstance(allowed[field], list):
            fail(f"{path}: allowed_surfaces.{field} must be a list")
    admission = record.get("admission", {})
    if admission.get("environment") == "production" and admission.get("decision") == "allowed":
        refs = record.get("trust_chain_refs", {})
        missing = sorted(key for key in REQUIRED_TRUST_CHAIN_REFS if not refs.get(key))
        if missing:
            fail(f"{path}: allowed production agent binding missing Trust Chain refs: {missing}")


def validate_preview(record: dict[str, Any], path: Path) -> None:
    validate_common(record, path)
    admission = record["admission"]
    if admission.get("environment") != "preview":
        fail(f"{path}: preview fixture requires environment=preview")
    if admission.get("decision") != "allowed":
        fail(f"{path}: preview fixture requires decision=allowed")
    if admission.get("review_required") is not True:
        fail(f"{path}: preview fixture requires review_required=true")
    profile = record["capability_profile"]
    if profile.get("autonomy_tier") != "review_required":
        fail(f"{path}: preview fixture autonomy_tier must be review_required")
    if profile.get("effect_tier") != "propose":
        fail(f"{path}: preview fixture effect_tier must be propose")
    refs = record.get("trust_chain_refs", {})
    missing = sorted(key for key in REQUIRED_TRUST_CHAIN_REFS if not refs.get(key))
    if missing:
        fail(f"{path}: preview fixture missing Trust Chain refs: {missing}")


def validate_blocked(record: dict[str, Any], path: Path) -> None:
    validate_common(record, path)
    admission = record["admission"]
    if admission.get("environment") != "production":
        fail(f"{path}: blocked fixture requires environment=production")
    if admission.get("decision") != "blocked":
        fail(f"{path}: blocked fixture requires decision=blocked")
    if admission.get("review_required") is not True:
        fail(f"{path}: blocked fixture requires review_required=true")
    if not admission.get("revocation_or_downgrade_ref"):
        fail(f"{path}: blocked fixture requires downgrade or revocation ref")
    if record.get("agent", {}).get("status") not in {"reduced", "suspended", "revoked"}:
        fail(f"{path}: blocked fixture must reduce, suspend, or revoke agent status")
    refs = record.get("trust_chain_refs", {})
    if refs.get("agentplane_validation_ref") is not None:
        fail(f"{path}: blocked fixture must not carry agentplane_validation_ref")
    if refs.get("model_admission_ref") is not None:
        fail(f"{path}: blocked fixture must not carry model_admission_ref")
    remediation = record.get("remediation", [])
    if not isinstance(remediation, list) or not remediation:
        fail(f"{path}: blocked fixture requires remediation")
    for item in remediation:
        if item.get("required_before_admission") is not True:
            fail(f"{path}: remediation must be required before admission")
        if not item.get("authority"):
            fail(f"{path}: remediation requires authority")


def main() -> int:
    try:
        schema = load_json(SCHEMA)
        preview = load_json(PREVIEW_FIXTURE)
        blocked = load_json(BLOCKED_FIXTURE)
        validate_schema(schema, preview)
        validate_schema(schema, blocked)
        validate_preview(preview, PREVIEW_FIXTURE)
        validate_blocked(blocked, BLOCKED_FIXTURE)
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2
    print("OK: Trust Chain agent manifest bindings passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
