from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
    agent = json.loads((ROOT / "examples" / "agent-spec.example.json").read_text(encoding="utf-8"))
    spec = agent["spec"]
    assert spec["toolGrantRefs"] == ["grant://agent/demo-analyst/model-route-read"]
    assert spec["revocationRef"] == "revocation://agent/demo-analyst/current"
    assert "surface://model-routing/demo" in spec["allowedSurfaceRefs"]


def test_tool_grant_is_constrained_and_reference_only() -> None:
    grant = json.loads((ROOT / "examples" / "tool-grant.example.json").read_text(encoding="utf-8"))
    constraints = set(grant["spec"]["constraints"])
    assert "no-live-provider-call" in constraints
    assert "no-secret-access" in constraints
    assert "evidence-required" in constraints


def test_session_authority_can_be_revoked_by_record() -> None:
    session = json.loads((ROOT / "examples" / "session-authority.example.json").read_text(encoding="utf-8"))
    revocation = json.loads((ROOT / "examples" / "revocation-record.example.json").read_text(encoding="utf-8"))
    assert session["spec"]["agentId"] == revocation["spec"]["agentId"]
    assert revocation["spec"]["status"] == "not-revoked"
