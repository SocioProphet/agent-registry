from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOOKUP = ROOT / "tools" / "authority_state_lookup.py"
STATE_DIR = ROOT / "contracts" / "trustops"
ACTIVE_STATE = STATE_DIR / "agent-authority-current-state.active.example.json"
SUSPENDED_STATE = STATE_DIR / "agent-authority-current-state.suspended.example.json"
RAW_RECEIPT_STATE = STATE_DIR / "agent-authority-current-state.raw-receipt.invalid.json"


def run_lookup(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LOOKUP), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_lookup_active_state_by_status() -> None:
    result = run_lookup(
        "get",
        "agent-registry://agent-alpha",
        "--status",
        "active",
        "--source-dir",
        str(STATE_DIR),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "AgentAuthorityStateLookupResult"
    assert payload["ok"] is True
    assert payload["mode"] == "readonly"
    assert payload["authority_status"] == "active"
    assert payload["authority_state"]["recordType"] == "AgentAuthorityCurrentState"
    assert "authority_mutation" in payload["non_goals"]


def test_lookup_explicit_state_file() -> None:
    result = run_lookup(
        "get",
        "agent-registry://agent-alpha",
        "--state-file",
        str(SUSPENDED_STATE),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["authority_status"] == "suspended"
    assert payload["state_file"] == str(SUSPENDED_STATE)


def test_lookup_ambiguous_without_status_fails_closed() -> None:
    result = run_lookup(
        "get",
        "agent-registry://agent-alpha",
        "--source-dir",
        str(STATE_DIR),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["recordType"] == "AgentAuthorityStateLookupError"
    assert payload["ok"] is False
    assert payload["reason_code"] == "authority_state_ambiguous"


def test_lookup_missing_state_fails_closed(tmp_path: Path) -> None:
    result = run_lookup(
        "get",
        "agent-registry://missing-agent",
        "--source-dir",
        str(tmp_path),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["reason_code"] == "authority_state_not_found"


def test_lookup_rejects_raw_receipt_derived_state() -> None:
    result = run_lookup(
        "get",
        "agent-registry://agent-alpha",
        "--state-file",
        str(RAW_RECEIPT_STATE),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["reason_code"] == "authority_state_invalid"
    assert "raw TrustOps receipt" in payload["message"]


def test_lookup_agent_mismatch_fails_closed() -> None:
    result = run_lookup(
        "get",
        "agent-registry://different-agent",
        "--state-file",
        str(ACTIVE_STATE),
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["reason_code"] == "authority_state_agent_mismatch"
