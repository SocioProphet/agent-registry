#!/usr/bin/env python3
"""Validate FraudAgentAdmissionProfile fixtures.

The validator is stdlib-only and enforces the admission boundaries that matter
for Fraud Decision Intelligence agents:

- report-only agents can summarize and recommend, not execute live controls;
- human-impacting or live-control authority requires policy authorization;
- memory writeback requires review receipt;
- model scores, graph paths, and benchmarks must remain non-proof signals.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "fraud-agent-admission-profile.v0.1.schema.json"
VALID_EXAMPLE = ROOT / "examples" / "fraud-agent-admission-profile.report-only.example.json"
INVALID_EXAMPLES = {
    ROOT / "examples" / "fraud-agent-admission-profile.human-impact-no-policy.invalid.json": "human-impacting authority without policy authorization",
    ROOT / "examples" / "fraud-agent-admission-profile.memory-writeback-unreviewed.invalid.json": "memory writeback without review receipt",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_fields(obj: dict[str, Any], fields: set[str], path: str) -> None:
    missing = sorted(fields - set(obj))
    require(not missing, f"{path}: missing fields {missing}")


def validate_profile(path: Path, doc: dict[str, Any]) -> None:
    require(doc.get("apiVersion") == "agent-registry.socioprophet.ai/v0.1", f"{path.name}: apiVersion invalid")
    require(doc.get("kind") == "FraudAgentAdmissionProfile", f"{path.name}: kind invalid")

    metadata = doc.get("metadata", {})
    require_fields(metadata, {"profileId", "createdAt", "capabilityRef", "doctrineRef", "ontologyRef", "modelGovernanceRef"}, f"{path.name}: metadata")
    require(str(metadata["profileId"]).startswith("urn:socioprophet:agent-admission:fraud:"), f"{path.name}: profileId must be fraud admission URN")
    require(metadata["capabilityRef"] == "fraud-decision-intelligence-control-plane", f"{path.name}: capabilityRef invalid")
    require("ProCybernetica" in metadata["doctrineRef"], f"{path.name}: doctrineRef must anchor ProCybernetica doctrine")
    require("ontogenesis" in metadata["ontologyRef"], f"{path.name}: ontologyRef must anchor Ontogenesis fraud ontology")
    require("model-governance-ledger" in metadata["modelGovernanceRef"], f"{path.name}: modelGovernanceRef must anchor model-governance-ledger")

    spec = doc.get("spec", {})
    require_fields(spec, {"agent", "allowedCapabilities", "gatedCapabilities", "prohibitedCapabilities", "requiredReceipts", "claimBoundaries", "memoryWriteback"}, f"{path.name}: spec")

    agent = spec["agent"]
    require_fields(agent, {"agentRef", "agentClass", "authorityMode"}, f"{path.name}: agent")
    authority = agent["authorityMode"]
    require(authority in {"report-only", "recommendation-only", "policy-gated-action"}, f"{path.name}: invalid authorityMode")

    allowed = set(spec.get("allowedCapabilities", []))
    gated = set(spec.get("gatedCapabilities", []))
    prohibited = set(spec.get("prohibitedCapabilities", []))

    require(allowed, f"{path.name}: allowedCapabilities must be non-empty")
    for required_prohibition in {"model_score_as_proof", "benchmark_as_production_validation"}:
        require(required_prohibition in prohibited, f"{path.name}: prohibitedCapabilities must include {required_prohibition}")

    for dangerous in {"human_impacting_action", "live_control_action", "private_evidence_ingest", "memory_writeback", "label_canonization", "scenario_to_rule_promotion"}:
        require(dangerous not in allowed, f"{path.name}: {dangerous} cannot be directly allowed")

    if authority in {"report-only", "recommendation-only"}:
        require("live_control_action" not in allowed, f"{path.name}: report/recommendation agents cannot execute live controls")

    receipts = spec["requiredReceipts"]
    require_fields(receipts, {"agentAdmissionReceipt", "evidenceBundleRef", "decisionReceiptRef", "policyAuthorizationRef", "modelGovernanceLedgerRef"}, f"{path.name}: requiredReceipts")
    require(receipts.get("agentAdmissionReceipt"), f"{path.name}: agentAdmissionReceipt required")
    require(receipts.get("modelGovernanceLedgerRef"), f"{path.name}: modelGovernanceLedgerRef required")

    if authority == "policy-gated-action":
        require("human_impacting_action" in gated or "live_control_action" in gated, f"{path.name}: policy-gated action profile must gate human-impacting or live-control action")
        require(receipts.get("policyAuthorizationRef"), f"{path.name}: policy-gated action requires policyAuthorizationRef")

    boundaries = spec["claimBoundaries"]
    require(boundaries.get("modelScoreBoundary") == "risk_signal_not_proof", f"{path.name}: invalid modelScoreBoundary")
    require(boundaries.get("graphPathBoundary") == "relationship_evidence_not_attribution", f"{path.name}: invalid graphPathBoundary")
    require(boundaries.get("benchmarkBoundary") == "not_production_validation", f"{path.name}: invalid benchmarkBoundary")
    require(boundaries.get("labelBoundary") == "requires_provenance_and_review", f"{path.name}: invalid labelBoundary")
    require(boundaries.get("actionBoundary") == "human_impacting_actions_require_policy_authorization", f"{path.name}: invalid actionBoundary")

    memory = spec["memoryWriteback"]
    require_fields(memory, {"allowed", "requiresReview", "reviewReceiptRef"}, f"{path.name}: memoryWriteback")
    if memory.get("allowed") is True:
        require(memory.get("requiresReview") is True, f"{path.name}: memory writeback requires review")
        require(memory.get("reviewReceiptRef"), f"{path.name}: memory writeback requires reviewReceiptRef")
    else:
        require(memory.get("reviewReceiptRef") in {None, ""} or memory.get("requiresReview") is True, f"{path.name}: disabled memory writeback should not carry unreviewed receipt semantics")


def main() -> int:
    load_json(SCHEMA)

    try:
        validate_profile(VALID_EXAMPLE.relative_to(ROOT), load_json(VALID_EXAMPLE))
        print(f"ok: {VALID_EXAMPLE.relative_to(ROOT)}")

        for invalid_path, expected_reason in INVALID_EXAMPLES.items():
            try:
                validate_profile(invalid_path.relative_to(ROOT), load_json(invalid_path))
            except ValidationError as exc:
                print(f"ok: rejected {invalid_path.relative_to(ROOT)} ({expected_reason}): {exc}")
                continue
            raise ValidationError(f"{invalid_path.relative_to(ROOT)} unexpectedly passed validation")
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 1

    print("Fraud agent admission profile validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
