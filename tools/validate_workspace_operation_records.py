#!/usr/bin/env python3
"""Validate workspace-operation agent registry records.

Checks all nine record kinds required for Workspace Operation Plane integration:
  AgentRegistration, AgentCapabilityDeclaration, AgentOperationScope,
  AgentDelegationGrant, AgentToolGrant, AgentBudgetPolicy,
  AgentAuditProfile, AgentRevocationRecord, AgentOperationSessionBinding.

Uses only the Python standard library.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WS_EXAMPLES = ROOT / "examples" / "workspace-operations"

EXAMPLES = [
    WS_EXAMPLES / "agent-registrations.example.json",
    WS_EXAMPLES / "capability-declarations.example.json",
    WS_EXAMPLES / "operation-scopes.example.json",
    WS_EXAMPLES / "delegation-grants.example.json",
    WS_EXAMPLES / "tool-grants.example.json",
    WS_EXAMPLES / "budget-policies.example.json",
    WS_EXAMPLES / "audit-profiles.example.json",
    WS_EXAMPLES / "revocation-records.example.json",
    WS_EXAMPLES / "session-bindings.example.json",
]

ALLOWED_AGENT_KINDS = {"codex", "copilot", "human", "local-cli", "system"}
ALLOWED_AUDIT_LEVELS = {"none", "summary", "standard", "full"}
ALLOWED_REVOCATION_STATES = {"active", "revoked", "suspended"}
ALLOWED_SESSION_STATUSES = {"active", "expired", "revoked"}

REQUIRED_AGENT_REGISTRATION_SPEC = {"ownerRef", "policyProfile", "revocationState", "evidenceRef", "revocationRef"}
REQUIRED_CAPABILITY_DECLARATION_SPEC = {"agentId", "allowedOperationTypes", "allowedTools", "allowedArtifactTypes", "policyProfile", "evidenceRef"}
REQUIRED_OPERATION_SCOPE_SPEC = {"agentId", "allowedOperationTypes", "allowedArtifactTypes", "policyProfile", "evidenceRef"}
REQUIRED_DELEGATION_GRANT_SPEC = {"agentId", "delegatedBy", "allowedOperationTypes", "allowedArtifactTypes", "policyProfile", "expiresAt", "revocationState", "evidenceRef"}
REQUIRED_TOOL_GRANT_SPEC = {"agentId", "allowedTools", "scope", "constraints", "expiresAt", "evidenceRef"}
REQUIRED_BUDGET_POLICY_SPEC = {"agentId", "defaultBudget", "maxConcurrency", "policyProfile", "evidenceRef"}
REQUIRED_AUDIT_PROFILE_SPEC = {"agentId", "auditLevel", "policyProfile", "evidenceRef"}
REQUIRED_REVOCATION_RECORD_SPEC = {"agentId", "revocationState", "revokedOperationTypes", "revokedTools", "reasonCodes", "evidenceRef"}
REQUIRED_SESSION_BINDING_SPEC = {"agentId", "operationScopeRef", "toolGrantRefs", "budgetPolicyRef", "auditProfileRef", "status", "evidenceRef"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def require_fields(label: str, mapping: dict, required: set[str]) -> int:
    missing = sorted(required - set(mapping))
    if missing:
        return fail(f"{label}: missing fields {missing}")
    return 0


def record_label(path: Path, index: int | None = None) -> str:
    rel = path.relative_to(ROOT)
    return f"{rel}[{index}]" if index is not None else str(rel)


def validate_record(doc: dict[str, Any], label: str) -> int:
    if doc.get("apiVersion") != "agentregistry.socioprophet.dev/v1":
        return fail(f"{label}: apiVersion invalid")
    kind = doc.get("kind")
    metadata = doc.get("metadata", {})
    spec = doc.get("spec", {})

    if kind == "AgentRegistration":
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        if metadata.get("agentKind") not in ALLOWED_AGENT_KINDS:
            return fail(f"{label}: metadata.agentKind invalid")
        if not metadata.get("version"):
            return fail(f"{label}: metadata.version required")
        rc = require_fields(label, spec, REQUIRED_AGENT_REGISTRATION_SPEC)
        if rc:
            return rc
        if spec["revocationState"] not in ALLOWED_REVOCATION_STATES:
            return fail(f"{label}: spec.revocationState invalid")

    elif kind == "AgentCapabilityDeclaration":
        if not metadata.get("declarationId"):
            return fail(f"{label}: metadata.declarationId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        rc = require_fields(label, spec, REQUIRED_CAPABILITY_DECLARATION_SPEC)
        if rc:
            return rc
        if not spec["allowedOperationTypes"]:
            return fail(f"{label}: allowedOperationTypes must be non-empty")
        if not spec["allowedTools"]:
            return fail(f"{label}: allowedTools must be non-empty")
        if not spec["allowedArtifactTypes"]:
            return fail(f"{label}: allowedArtifactTypes must be non-empty")

    elif kind == "AgentOperationScope":
        if not metadata.get("scopeId"):
            return fail(f"{label}: metadata.scopeId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        rc = require_fields(label, spec, REQUIRED_OPERATION_SCOPE_SPEC)
        if rc:
            return rc
        if not spec["allowedOperationTypes"]:
            return fail(f"{label}: allowedOperationTypes must be non-empty")
        if not spec["allowedArtifactTypes"]:
            return fail(f"{label}: allowedArtifactTypes must be non-empty")

    elif kind == "AgentDelegationGrant":
        if not metadata.get("grantId"):
            return fail(f"{label}: metadata.grantId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        rc = require_fields(label, spec, REQUIRED_DELEGATION_GRANT_SPEC)
        if rc:
            return rc
        if not spec["delegatedBy"]:
            return fail(f"{label}: delegatedBy must be non-empty")
        if spec["revocationState"] not in {"active", "revoked", "expired"}:
            return fail(f"{label}: spec.revocationState invalid")
        if not spec["allowedOperationTypes"]:
            return fail(f"{label}: allowedOperationTypes must be non-empty")

    elif kind == "AgentToolGrant":
        if not metadata.get("grantId"):
            return fail(f"{label}: metadata.grantId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        rc = require_fields(label, spec, REQUIRED_TOOL_GRANT_SPEC)
        if rc:
            return rc
        if not spec["allowedTools"]:
            return fail(f"{label}: allowedTools must be non-empty")
        if not spec["constraints"]:
            return fail(f"{label}: constraints must be non-empty")
        if "evidence-required" not in set(spec["constraints"]):
            return fail(f"{label}: evidence-required constraint is mandatory")

    elif kind == "AgentBudgetPolicy":
        if not metadata.get("policyId"):
            return fail(f"{label}: metadata.policyId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        rc = require_fields(label, spec, REQUIRED_BUDGET_POLICY_SPEC)
        if rc:
            return rc
        budget = spec.get("defaultBudget", {})
        for field in ("maxTokensPerOperation", "maxOperationsPerSession", "maxArtifactsPerOperation"):
            if not isinstance(budget.get(field), int) or budget[field] < 1:
                return fail(f"{label}: defaultBudget.{field} must be a positive integer")
        if not isinstance(spec.get("maxConcurrency"), int) or spec["maxConcurrency"] < 1:
            return fail(f"{label}: maxConcurrency must be a positive integer")

    elif kind == "AgentAuditProfile":
        if not metadata.get("profileId"):
            return fail(f"{label}: metadata.profileId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        rc = require_fields(label, spec, REQUIRED_AUDIT_PROFILE_SPEC)
        if rc:
            return rc
        if spec["auditLevel"] not in ALLOWED_AUDIT_LEVELS:
            return fail(f"{label}: auditLevel invalid")

    elif kind == "AgentRevocationRecord":
        if not metadata.get("revocationId"):
            return fail(f"{label}: metadata.revocationId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        if not metadata.get("createdAt"):
            return fail(f"{label}: metadata.createdAt required")
        rc = require_fields(label, spec, REQUIRED_REVOCATION_RECORD_SPEC)
        if rc:
            return rc
        if spec["revocationState"] not in {"not-revoked", "revoked"}:
            return fail(f"{label}: revocationState invalid")
        if not spec["reasonCodes"]:
            return fail(f"{label}: reasonCodes must be non-empty")

    elif kind == "AgentOperationSessionBinding":
        if not metadata.get("sessionId"):
            return fail(f"{label}: metadata.sessionId required")
        if not metadata.get("agentId"):
            return fail(f"{label}: metadata.agentId required")
        if not metadata.get("createdAt"):
            return fail(f"{label}: metadata.createdAt required")
        rc = require_fields(label, spec, REQUIRED_SESSION_BINDING_SPEC)
        if rc:
            return rc
        if spec["status"] not in ALLOWED_SESSION_STATUSES:
            return fail(f"{label}: status invalid")
        if not spec["toolGrantRefs"]:
            return fail(f"{label}: toolGrantRefs must be non-empty")

    else:
        return fail(f"{label}: unknown kind {kind!r}")

    return 0


def iter_records(path: Path):
    doc = load(path)
    if isinstance(doc, list):
        for index, record in enumerate(doc):
            yield record, record_label(path, index)
    else:
        yield doc, record_label(path)


def validate_cross_refs() -> int:
    """Verify that session bindings reference registered agents, scopes, and tool grants."""
    registrations = load(WS_EXAMPLES / "agent-registrations.example.json")
    tool_grants = load(WS_EXAMPLES / "tool-grants.example.json")
    operation_scopes = load(WS_EXAMPLES / "operation-scopes.example.json")
    session_bindings = load(WS_EXAMPLES / "session-bindings.example.json")
    revocation_records = load(WS_EXAMPLES / "revocation-records.example.json")

    agent_ids = {r["metadata"]["agentId"] for r in registrations}
    tool_grant_ids = {g["metadata"]["grantId"] for g in tool_grants}
    scope_ids = {s["metadata"]["scopeId"] for s in operation_scopes}
    revocation_ids = {r["metadata"]["revocationId"] for r in revocation_records}

    for reg in registrations:
        rev_ref = reg["spec"]["revocationRef"]
        if rev_ref not in revocation_ids:
            return fail(f"workspace-operations: AgentRegistration {reg['metadata']['agentId']} references missing revocationRef {rev_ref!r}")

    for binding in session_bindings:
        agent_id = binding["spec"]["agentId"]
        if agent_id not in agent_ids:
            return fail(f"workspace-operations: session binding references unregistered agent {agent_id!r}")
        scope_ref = binding["spec"]["operationScopeRef"]
        if scope_ref not in scope_ids:
            return fail(f"workspace-operations: session binding references unknown scope {scope_ref!r}")
        for grant_ref in binding["spec"]["toolGrantRefs"]:
            if grant_ref not in tool_grant_ids:
                return fail(f"workspace-operations: session binding references unknown tool grant {grant_ref!r}")

    return 0


def main() -> int:
    count = 0
    for path in EXAMPLES:
        for record, label in iter_records(path):
            rc = validate_record(record, label)
            if rc:
                return rc
            count += 1

    rc = validate_cross_refs()
    if rc:
        return rc

    print(f"OK: validated {count} workspace-operation registry records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
