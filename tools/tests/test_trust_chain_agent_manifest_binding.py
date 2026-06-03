from __future__ import annotations

import json
from pathlib import Path

from tools.validate_trust_chain_agent_manifest_binding import main as validate_trust_chain_agent_manifest_binding


ROOT = Path(__file__).resolve().parents[2]
PREVIEW_FIXTURE = ROOT / "examples" / "trust-chain-agent-manifest-binding.preview.example.json"
BLOCKED_FIXTURE = ROOT / "examples" / "trust-chain-agent-manifest-binding.blocked.json"


def test_trust_chain_agent_manifest_binding_validator() -> None:
    assert validate_trust_chain_agent_manifest_binding() == 0


def test_preview_binding_is_allowed_but_review_required() -> None:
    fixture = json.loads(PREVIEW_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["admission"]["environment"] == "preview"
    assert fixture["admission"]["decision"] == "allowed"
    assert fixture["admission"]["review_required"] is True
    assert fixture["capability_profile"]["autonomy_tier"] == "review_required"
    assert fixture["capability_profile"]["effect_tier"] == "propose"


def test_blocked_binding_reduces_authority_and_requires_remediation() -> None:
    fixture = json.loads(BLOCKED_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["admission"]["environment"] == "production"
    assert fixture["admission"]["decision"] == "blocked"
    assert fixture["agent"]["status"] == "reduced"
    assert fixture["trust_chain_refs"]["agentplane_validation_ref"] is None
    assert fixture["trust_chain_refs"]["model_admission_ref"] is None
    assert fixture["remediation"]
    assert all(item["required_before_admission"] is True for item in fixture["remediation"])
