from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_agent_registry_examples_validate() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_agent_registry_examples.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert "OK: validated" in result.stdout


def test_agent_spec_references_tool_grant_and_revocation() -> None:
    agent = load_json(ROOT / "examples" / "agent-spec.example.json")
    spec = agent["spec"]
    assert spec["toolGrantRefs"] == ["grant://agent/demo-analyst/model-route-read"]
    assert spec["revocationRef"] == "revocation://agent/demo-analyst/current"
    assert "surface://model-routing/demo" in spec["allowedSurfaceRefs"]


def test_tool_grant_is_constrained_and_reference_only() -> None:
    grant = load_json(ROOT / "examples" / "tool-grant.example.json")
    constraints = set(grant["spec"]["constraints"])
    assert "no-live-provider-call" in constraints
    assert "no-secret-access" in constraints
    assert "evidence-required" in constraints


def test_session_authority_can_be_revoked_by_record() -> None:
    session = load_json(ROOT / "examples" / "session-authority.example.json")
    revocation = load_json(ROOT / "examples" / "revocation-record.example.json")
    assert session["spec"]["agentId"] == revocation["spec"]["agentId"]
    assert revocation["spec"]["status"] == "not-revoked"


def test_professional_intelligence_agent_specs_are_registered() -> None:
    agents = load_json(ROOT / "examples" / "professional-intelligence" / "agent-specs.example.json")
    agent_ids = {agent["metadata"]["agentId"] for agent in agents}
    assert agent_ids == {
        "agent://professional-intelligence/opportunity-review-agent",
        "agent://professional-intelligence/relationship-agent",
        "agent://professional-intelligence/policy-review-agent",
        "agent://professional-intelligence/workspace-setup-agent",
    }


def test_professional_intelligence_tool_grants_are_scoped_and_evidence_bound() -> None:
    grants = load_json(ROOT / "examples" / "professional-intelligence" / "tool-grants.example.json")
    assert len(grants) == 5
    for grant in grants:
        constraints = set(grant["spec"]["constraints"])
        assert "evidence-required" in constraints
        assert grant["spec"]["scope"] in {"read-evaluate-only", "draft-update-only", "read-only", "evaluate-only", "create-draft-only"}


def test_professional_intelligence_agent_grant_cross_refs() -> None:
    agents = load_json(ROOT / "examples" / "professional-intelligence" / "agent-specs.example.json")
    grants = load_json(ROOT / "examples" / "professional-intelligence" / "tool-grants.example.json")
    grant_ids = {grant["metadata"]["grantId"] for grant in grants}
    for agent in agents:
        for grant_ref in agent["spec"]["toolGrantRefs"]:
            assert grant_ref in grant_ids


def test_professional_intelligence_session_and_revocation_reference_registered_agent() -> None:
    agents = load_json(ROOT / "examples" / "professional-intelligence" / "agent-specs.example.json")
    grants = load_json(ROOT / "examples" / "professional-intelligence" / "tool-grants.example.json")
    session = load_json(ROOT / "examples" / "professional-intelligence" / "session-authority.example.json")
    revocation = load_json(ROOT / "examples" / "professional-intelligence" / "revocation-record.example.json")

    agent_ids = {agent["metadata"]["agentId"] for agent in agents}
    grant_ids = {grant["metadata"]["grantId"] for grant in grants}

    assert session["spec"]["agentId"] in agent_ids
    assert revocation["spec"]["agentId"] in agent_ids
    assert set(session["spec"]["activeToolGrantRefs"]).issubset(grant_ids)
    assert revocation["spec"]["status"] == "not-revoked"
