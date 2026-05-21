from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS_EXAMPLES = ROOT / "examples" / "workspace-operations"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_workspace_operation_records_validate() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_workspace_operation_records.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "OK: validated" in result.stdout


def test_agent_registrations_have_required_fields() -> None:
    registrations = load_json(WS_EXAMPLES / "agent-registrations.example.json")
    assert len(registrations) >= 1
    for reg in registrations:
        assert reg["kind"] == "AgentRegistration"
        assert reg["apiVersion"] == "agentregistry.socioprophet.dev/v1"
        meta = reg["metadata"]
        assert meta.get("agentId")
        assert meta.get("agentKind") in {"codex", "copilot", "human", "local-cli", "system"}
        assert meta.get("version")
        spec = reg["spec"]
        for field in ("ownerRef", "policyProfile", "revocationState", "evidenceRef", "revocationRef"):
            assert field in spec, f"missing {field} in AgentRegistration spec"


def test_capability_declarations_have_required_fields() -> None:
    declarations = load_json(WS_EXAMPLES / "capability-declarations.example.json")
    assert len(declarations) >= 1
    for decl in declarations:
        assert decl["kind"] == "AgentCapabilityDeclaration"
        spec = decl["spec"]
        assert spec.get("allowedOperationTypes"), "allowedOperationTypes must be non-empty"
        assert spec.get("allowedTools"), "allowedTools must be non-empty"
        assert spec.get("allowedArtifactTypes"), "allowedArtifactTypes must be non-empty"
        assert spec.get("policyProfile")
        assert spec.get("evidenceRef")


def test_operation_scopes_have_required_fields() -> None:
    scopes = load_json(WS_EXAMPLES / "operation-scopes.example.json")
    assert len(scopes) >= 1
    for scope in scopes:
        assert scope["kind"] == "AgentOperationScope"
        spec = scope["spec"]
        assert spec.get("allowedOperationTypes"), "allowedOperationTypes must be non-empty"
        assert spec.get("allowedArtifactTypes"), "allowedArtifactTypes must be non-empty"


def test_delegation_grants_are_scoped_expiring_and_have_delegated_by() -> None:
    grants = load_json(WS_EXAMPLES / "delegation-grants.example.json")
    assert len(grants) >= 1
    for grant in grants:
        assert grant["kind"] == "AgentDelegationGrant"
        spec = grant["spec"]
        assert spec.get("delegatedBy"), "delegatedBy required"
        assert spec.get("expiresAt"), "expiresAt required"
        assert spec.get("revocationState") in {"active", "revoked", "expired"}
        assert spec.get("allowedOperationTypes"), "allowedOperationTypes must be non-empty"


def test_tool_grants_have_evidence_required_constraint() -> None:
    grants = load_json(WS_EXAMPLES / "tool-grants.example.json")
    assert len(grants) >= 1
    for grant in grants:
        assert grant["kind"] == "AgentToolGrant"
        spec = grant["spec"]
        assert spec.get("allowedTools"), "allowedTools must be non-empty"
        assert "evidence-required" in spec.get("constraints", []), "evidence-required constraint mandatory"
        assert spec.get("expiresAt"), "expiresAt required"


def test_budget_policies_have_budget_and_concurrency() -> None:
    policies = load_json(WS_EXAMPLES / "budget-policies.example.json")
    assert len(policies) >= 1
    for policy in policies:
        assert policy["kind"] == "AgentBudgetPolicy"
        spec = policy["spec"]
        budget = spec.get("defaultBudget", {})
        assert isinstance(budget.get("maxTokensPerOperation"), int)
        assert isinstance(budget.get("maxOperationsPerSession"), int)
        assert isinstance(budget.get("maxArtifactsPerOperation"), int)
        assert isinstance(spec.get("maxConcurrency"), int)
        assert spec["maxConcurrency"] >= 1


def test_audit_profiles_have_valid_audit_level() -> None:
    profiles = load_json(WS_EXAMPLES / "audit-profiles.example.json")
    assert len(profiles) >= 1
    for profile in profiles:
        assert profile["kind"] == "AgentAuditProfile"
        assert profile["spec"]["auditLevel"] in {"none", "summary", "standard", "full"}


def test_revocation_records_have_revocation_state() -> None:
    records = load_json(WS_EXAMPLES / "revocation-records.example.json")
    assert len(records) >= 1
    for record in records:
        assert record["kind"] == "AgentRevocationRecord"
        spec = record["spec"]
        assert spec.get("revocationState") in {"not-revoked", "revoked"}
        assert isinstance(spec.get("revokedOperationTypes"), list)
        assert isinstance(spec.get("revokedTools"), list)
        assert spec.get("reasonCodes"), "reasonCodes must be non-empty"


def test_session_bindings_reference_registered_agents() -> None:
    registrations = load_json(WS_EXAMPLES / "agent-registrations.example.json")
    tool_grants = load_json(WS_EXAMPLES / "tool-grants.example.json")
    operation_scopes = load_json(WS_EXAMPLES / "operation-scopes.example.json")
    session_bindings = load_json(WS_EXAMPLES / "session-bindings.example.json")

    agent_ids = {r["metadata"]["agentId"] for r in registrations}
    tool_grant_ids = {g["metadata"]["grantId"] for g in tool_grants}
    scope_ids = {s["metadata"]["scopeId"] for s in operation_scopes}

    for binding in session_bindings:
        assert binding["kind"] == "AgentOperationSessionBinding"
        spec = binding["spec"]
        assert spec["agentId"] in agent_ids, f"unregistered agent {spec['agentId']!r}"
        assert spec["operationScopeRef"] in scope_ids, f"unknown scope {spec['operationScopeRef']!r}"
        for grant_ref in spec["toolGrantRefs"]:
            assert grant_ref in tool_grant_ids, f"unknown tool grant {grant_ref!r}"
        assert spec["status"] in {"active", "expired", "revoked"}


def test_all_nine_workspace_operation_kinds_are_present() -> None:
    expected_kinds = {
        "AgentRegistration",
        "AgentCapabilityDeclaration",
        "AgentOperationScope",
        "AgentDelegationGrant",
        "AgentToolGrant",
        "AgentBudgetPolicy",
        "AgentAuditProfile",
        "AgentRevocationRecord",
        "AgentOperationSessionBinding",
    }
    found_kinds: set[str] = set()
    example_files = [
        "agent-registrations.example.json",
        "capability-declarations.example.json",
        "operation-scopes.example.json",
        "delegation-grants.example.json",
        "tool-grants.example.json",
        "budget-policies.example.json",
        "audit-profiles.example.json",
        "revocation-records.example.json",
        "session-bindings.example.json",
    ]
    for filename in example_files:
        records = load_json(WS_EXAMPLES / filename)
        for record in records:
            found_kinds.add(record["kind"])
    assert found_kinds == expected_kinds, f"missing kinds: {expected_kinds - found_kinds}"


def test_revocation_records_match_registered_agents() -> None:
    registrations = load_json(WS_EXAMPLES / "agent-registrations.example.json")
    revocation_records = load_json(WS_EXAMPLES / "revocation-records.example.json")

    revocation_ids = {r["metadata"]["revocationId"] for r in revocation_records}
    for reg in registrations:
        rev_ref = reg["spec"]["revocationRef"]
        assert rev_ref in revocation_ids, f"AgentRegistration references missing revocationRef {rev_ref!r}"
