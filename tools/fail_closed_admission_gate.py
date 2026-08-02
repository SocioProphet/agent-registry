#!/usr/bin/env python3
"""FailClosedAdmissionGate — realize INV-ACC-1 (no invisible authority).

Standard 030 (SocioProphet/socioprophet-agent-standards docs/standards/030),
invariant INV-ACC-1: *an agent that declares capabilities MUST resolve to a
registry admission entry.* Capability without admission = denied.

This gate is the enforcement of that invariant. Given a DeclaredCapabilityRecord
(what an agent claims it can do) and the registry's admission directory
(`agents/admissions/*.admission.json`), it returns:

  * admitted        (exit 0) -- a resolvable admission entry with
                                admission_status=admitted AND authority.granted=true.
  * review-required (exit 3) -- a resolvable admission entry that only *proposes*
                                admission (status=proposed): the agent is now
                                VISIBLE and tracked, but authority is NOT granted.
                                A proposed stub never authorizes.
  * denied          (exit 1) -- capability declared with NO resolvable admission
                                entry (the INV-ACC-1 violation: invisible
                                authority), or an admission entry that is
                                denied/revoked, or any malformed/ambiguous input.

It is fail-closed by construction: unknown agent, missing entry, invalid entry,
ambiguous entry, or any admission_status it does not explicitly recognize -> deny.
Only an explicit, resolvable, granted admission ever exits 0. It never fails open.

Exit codes: 0 = admitted, 3 = review-required, 1 = deny/error. 2 is deliberately
unused so it stays distinct from argparse's usage-error exit code.

Self-exclusion: the gate governs *agents* (DeclaredCapabilityRecords). It does
NOT treat the registry substrate as an agent under test -- this checker, the
admission manifests in agents/admissions/, and the admission schema are the
governance plane, not governed capability-bearing agents. `scan` only ingests
files whose recordType is DeclaredCapabilityRecord and skips everything else.

This gate records admission visibility. It does not grant live credentials,
mutate authority, sign off proposed stubs, or replace runtime/model/policy/
guardrail/AgentPlane authorities.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADMISSIONS_DIR = ROOT / "agents" / "admissions"
ADMISSION_SCHEMA = ROOT / "schemas" / "agent-admission-manifest.v0.1.schema.json"

DECLARED_RECORD_TYPE = "DeclaredCapabilityRecord"
ADMISSION_RECORD_TYPE = "AgentAdmissionManifest"

NON_GOALS = [
    "authority_mutation",
    "proposed_stub_sign_off",
    "live_credential_issuance",
    "agentplane_admission",
    "runtime_execution",
]

# admission_status -> gate verdict. Anything not listed here fails closed to deny.
STATUS_VERDICT = {
    "admitted": "admitted",  # promoted to allow only if authority.granted is also true
    "proposed": "review-required",
    "denied": "deny",
    "revoked": "deny",
}

EXIT_ADMITTED = 0
EXIT_DENY = 1
EXIT_REVIEW = 3

VERDICT_EXIT = {"admitted": EXIT_ADMITTED, "review-required": EXIT_REVIEW, "deny": EXIT_DENY}


class GateError(Exception):
    """Raised for unresolvable / malformed input. Always maps to a deny."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


# --------------------------------------------------------------------------- #
# Minimal, stdlib-only JSON-Schema structural validation (subset).            #
# Mirrors the vetted validator used by the other tools in this repo so the    #
# gate stays dependency-free (validate.yml installs pytest, not jsonschema).  #
# --------------------------------------------------------------------------- #

def _json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
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


def _type_matches(value: Any, expected: str) -> bool:
    actual = _json_type_name(value)
    if expected == "number":
        return actual in {"integer", "number"}
    return actual == expected


def _validate_schema(schema: dict[str, Any], value: Any, path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        raise GateError("schema_violation", f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise GateError("schema_violation", f"{path}: {value!r} not in enum {schema['enum']!r}")
    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_matches(value, item) for item in expected_types):
            raise GateError(
                "schema_violation",
                f"{path}: expected type {expected_types!r}, got {_json_type_name(value)!r}",
            )
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise GateError("schema_violation", f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise GateError("schema_violation", f"{path}: unexpected properties {extra!r}")
        additional = schema.get("additionalProperties")
        for key, item in value.items():
            child = properties.get(key)
            if child is None and isinstance(additional, dict):
                child = additional
            if child is not None:
                _validate_schema(child, item, f"{path}.{key}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise GateError("schema_violation", f"{path}: expected at least {schema['minItems']} items")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                _validate_schema(item_schema, item, f"{path}[{index}]")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GateError("input_missing", f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GateError("input_invalid_json", f"invalid JSON in {path}: {exc}") from exc


# --------------------------------------------------------------------------- #
# Admission index                                                             #
# --------------------------------------------------------------------------- #

def _validate_admission(record: dict[str, Any], where: str) -> None:
    schema = _load_json(ADMISSION_SCHEMA)
    _validate_schema(schema, record, where)
    status = record.get("admission_status")
    granted = record.get("authority", {}).get("granted")
    production = record.get("production_admitted")
    # Cross-field fail-closed invariants (the mini-validator ignores if/then):
    if status != "admitted":
        if granted is not False:
            raise GateError("admission_invariant", f"{where}: non-admitted status must have authority.granted=false")
        if production is not False:
            raise GateError("admission_invariant", f"{where}: non-admitted status must have production_admitted=false")
    if status == "admitted" and granted is not True:
        raise GateError("admission_invariant", f"{where}: admitted status requires authority.granted=true")


def build_admission_index(admissions_dir: Path) -> dict[str, dict[str, Any]]:
    """Map agent_id -> validated admission manifest. Fail closed on any bad entry.

    A duplicate agent_id is ambiguous authority and is rejected outright, so the
    gate can never silently pick one of two conflicting admission records.
    """
    index: dict[str, dict[str, Any]] = {}
    if not admissions_dir.is_dir():
        return index
    for path in sorted(admissions_dir.glob("*.admission.json")):
        record = _load_json(path)
        if not isinstance(record, dict) or record.get("recordType") != ADMISSION_RECORD_TYPE:
            raise GateError("admission_malformed", f"{path.name}: not an {ADMISSION_RECORD_TYPE}")
        _validate_admission(record, path.name)
        agent_id = record["agent_id"]
        if agent_id in index:
            raise GateError("admission_ambiguous", f"duplicate admission entry for agent_id {agent_id!r}")
        index[agent_id] = record
    return index


# --------------------------------------------------------------------------- #
# Core gate                                                                    #
# --------------------------------------------------------------------------- #

def _decision(
    *,
    verdict: str,
    reason_code: str,
    agent_id: str,
    declared_capabilities: list[str],
    admission_status: str | None,
    authority_granted: bool | None,
    authority_refs: list[str],
) -> dict[str, Any]:
    return {
        "schemaVersion": "agent-registry.fail-closed-admission-gate.v0.1",
        "recordType": "AdmissionGateDecision",
        "ok": verdict == "admitted",
        "invariant": "INV-ACC-1",
        "standard_ref": "socioprophet-agent-standards/docs/standards/030",
        "verdict": verdict,
        "reason_code": reason_code,
        "agent_id": agent_id,
        "declared_capabilities": declared_capabilities,
        "admission_status": admission_status,
        "authority_granted": authority_granted,
        "authority_refs": authority_refs,
        "non_goals": NON_GOALS,
    }


def evaluate_declared(record: dict[str, Any], index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Return a fail-closed admission decision for one DeclaredCapabilityRecord."""
    if not isinstance(record, dict) or record.get("recordType") != DECLARED_RECORD_TYPE:
        raise GateError("declared_malformed", f"not a {DECLARED_RECORD_TYPE}")
    agent_id = record.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        raise GateError("declared_no_agent_id", "declared record missing agent_id")
    caps = record.get("declared_capabilities")
    if not isinstance(caps, list):
        raise GateError("declared_bad_capabilities", "declared_capabilities must be a list")

    # An agent that declares NO capability holds no authority to gate.
    if len(caps) == 0:
        return _decision(
            verdict="admitted",
            reason_code="no_declared_capability",
            agent_id=agent_id,
            declared_capabilities=[],
            admission_status=None,
            authority_granted=None,
            authority_refs=[],
        )

    admission = index.get(agent_id)
    if admission is None:
        # INV-ACC-1 violation: capability declared, no resolvable admission entry.
        return _decision(
            verdict="deny",
            reason_code="invisible_authority_no_admission_entry",
            agent_id=agent_id,
            declared_capabilities=caps,
            admission_status=None,
            authority_granted=None,
            authority_refs=[],
        )

    status = admission.get("admission_status")
    granted = admission.get("authority", {}).get("granted")
    refs = list(admission.get("authority", {}).get("authority_refs", []))
    base_verdict = STATUS_VERDICT.get(status, "deny")  # unknown status -> deny

    if base_verdict == "admitted":
        # Belt-and-suspenders: admitted status must also carry granted authority.
        if granted is not True:
            return _decision(
                verdict="deny",
                reason_code="admitted_without_granted_authority",
                agent_id=agent_id,
                declared_capabilities=caps,
                admission_status=status,
                authority_granted=granted,
                authority_refs=refs,
            )
        if not refs:
            return _decision(
                verdict="deny",
                reason_code="admitted_without_authority_refs",
                agent_id=agent_id,
                declared_capabilities=caps,
                admission_status=status,
                authority_granted=granted,
                authority_refs=refs,
            )
        return _decision(
            verdict="admitted",
            reason_code="admitted_with_authority",
            agent_id=agent_id,
            declared_capabilities=caps,
            admission_status=status,
            authority_granted=granted,
            authority_refs=refs,
        )

    reason = {
        "review-required": "proposed_admission_pending_owner_sign_off",
        "deny": f"admission_status_{status}",
    }[base_verdict]
    return _decision(
        verdict=base_verdict,
        reason_code=reason,
        agent_id=agent_id,
        declared_capabilities=caps,
        admission_status=status,
        authority_granted=granted,
        authority_refs=refs,
    )


def _deny_from_error(exc: GateError, agent_id: str = "unknown") -> dict[str, Any]:
    return _decision(
        verdict="deny",
        reason_code=exc.reason_code,
        agent_id=agent_id,
        declared_capabilities=[],
        admission_status=None,
        authority_granted=None,
        authority_refs=[],
    )


# --------------------------------------------------------------------------- #
# Runtime resolution by agent ref                                             #
#                                                                             #
# The CI `check`/`scan` commands gate DeclaredCapabilityRecord *files*. The   #
# runtime authorize surface (tools/authorize.py) instead knows an agent only  #
# by its canonical `agent-registry://` ref at request time. These helpers let #
# that surface ask the SAME gate the same question -- "is this agent          #
# admitted?" -- so INV-ACC-1 is enforced at admission time, not just in CI.   #
# --------------------------------------------------------------------------- #

def find_admission_by_ref(index: dict[str, dict[str, Any]], agent_ref: str) -> dict[str, Any] | None:
    """Resolve the admission manifest for a runtime agent reference.

    Admission manifests are keyed by ``agent_id`` but may carry an optional
    canonical ``agent_ref``. The runtime authorize surface presents an
    ``agent-registry://`` ref, so match on ``agent_ref`` first, then fall back
    to ``agent_id``. Fail closed: a ref that resolves to zero OR more than one
    manifest is unresolvable/ambiguous authority and returns ``None`` (the
    caller denies).
    """
    if not agent_ref:
        return None
    hits = [
        manifest
        for manifest in index.values()
        if manifest.get("agent_ref") == agent_ref or manifest.get("agent_id") == agent_ref
    ]
    if len(hits) != 1:
        return None
    return hits[0]


def resolve_admission_for_ref(agent_ref: str, admissions_dir: Path) -> dict[str, Any]:
    """Fail-closed admission decision for a runtime agent ref (INV-ACC-1).

    Wraps ``build_admission_index`` + ``evaluate_declared`` so the RUNTIME
    authorize path and the CI check/scan share ONE decision function -- the
    runtime gate can never drift from what CI enforces. Any resolution failure
    (unreadable/malformed index, unknown ref, ambiguous ref) -> deny. A capable
    agent with no resolvable admission entry -> deny with reason
    ``invisible_authority_no_admission_entry``.
    """
    try:
        index = build_admission_index(admissions_dir)
    except GateError as exc:
        return _deny_from_error(exc, agent_ref)

    manifest = find_admission_by_ref(index, agent_ref)
    if manifest is None:
        return _decision(
            verdict="deny",
            reason_code="invisible_authority_no_admission_entry",
            agent_id=agent_ref,
            declared_capabilities=[],
            admission_status=None,
            authority_granted=None,
            authority_refs=[],
        )

    # Evaluate the resolved manifest through the exact same verdict logic CI
    # uses: synthesize the agent's DeclaredCapabilityRecord from the manifest
    # and gate it against the index it came from.
    declared = {
        "recordType": DECLARED_RECORD_TYPE,
        "agent_id": manifest["agent_id"],
        "declared_capabilities": manifest.get("declared_capabilities", []),
    }
    try:
        decision = evaluate_declared(declared, index)
    except GateError as exc:
        return _deny_from_error(exc, agent_ref)
    # Preserve the runtime-facing identity in the decision surfaced to callers.
    decision["agent_ref"] = agent_ref
    return decision


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_check(args: argparse.Namespace) -> int:
    try:
        index = build_admission_index(Path(args.admissions_dir))
        record = _load_json(Path(args.declared_file))
        decision = evaluate_declared(record, index)
    except GateError as exc:
        decision = _deny_from_error(exc)
    emit(decision)
    return VERDICT_EXIT[decision["verdict"]]


def command_scan(args: argparse.Namespace) -> int:
    """Scan a directory of declared records against the admissions index.

    Aggregate verdict is the worst case found: any deny -> deny (exit 1);
    else any review-required -> review-required (exit 3); else admitted (0).
    Self-exclusion: files that are not DeclaredCapabilityRecords are skipped,
    so the substrate (admission manifests, this checker) is never gated.
    """
    declared_dir = Path(args.declared_dir)
    try:
        index = build_admission_index(Path(args.admissions_dir))
    except GateError as exc:
        emit({"verdict": "deny", "reason_code": exc.reason_code, "error": str(exc)})
        return EXIT_DENY

    results: list[dict[str, Any]] = []
    skipped: list[str] = []
    for path in sorted(declared_dir.glob("*.json")):
        raw = _load_json(path)
        candidates = raw if isinstance(raw, list) else [raw]
        for item in candidates:
            if not isinstance(item, dict) or item.get("recordType") != DECLARED_RECORD_TYPE:
                skipped.append(path.name)  # self-exclusion: not an agent under test
                continue
            try:
                decision = evaluate_declared(item, index)
            except GateError as exc:
                decision = _deny_from_error(exc, str(item.get("agent_id", "unknown")))
            decision["_source_file"] = path.name
            results.append(decision)

    denied = [r for r in results if r["verdict"] == "deny"]
    review = [r for r in results if r["verdict"] == "review-required"]
    admitted = [r for r in results if r["verdict"] == "admitted"]

    if denied:
        aggregate = "deny"
    elif review:
        aggregate = "review-required"
    else:
        aggregate = "admitted"

    emit(
        {
            "schemaVersion": "agent-registry.fail-closed-admission-gate.scan.v0.1",
            "recordType": "AdmissionGateScan",
            "invariant": "INV-ACC-1",
            "aggregate_verdict": aggregate,
            "counts": {
                "scanned": len(results),
                "admitted": len(admitted),
                "review_required": len(review),
                "denied": len(denied),
                "skipped_non_agent_files": len(skipped),
            },
            "denied_agents": [
                {"agent_id": r["agent_id"], "reason_code": r["reason_code"], "source": r["_source_file"]}
                for r in denied
            ],
            "review_required_agents": [
                {"agent_id": r["agent_id"], "reason_code": r["reason_code"], "source": r["_source_file"]}
                for r in review
            ],
            "admitted_agents": [
                {"agent_id": r["agent_id"], "source": r["_source_file"]} for r in admitted
            ],
        }
    )
    return VERDICT_EXIT[aggregate]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fail-closed-admission-gate",
        description="Fail-closed admission gate for INV-ACC-1 (no invisible authority).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Gate one DeclaredCapabilityRecord against the admissions index.")
    check.add_argument("declared_file")
    check.add_argument("--admissions-dir", default=str(DEFAULT_ADMISSIONS_DIR))
    check.set_defaults(func=command_check)

    scan = sub.add_parser("scan", help="Gate a directory of declared records; aggregate worst-case verdict.")
    scan.add_argument("declared_dir")
    scan.add_argument("--admissions-dir", default=str(DEFAULT_ADMISSIONS_DIR))
    scan.set_defaults(func=command_scan)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
