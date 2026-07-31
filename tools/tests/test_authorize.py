"""Fail-closed authorize surface tests.

These assert the property that matters for a governance gate: the authorize
surface only ever returns `allow` for a resolvable, valid, sufficiently-
authorized state, and returns `deny` for every failure mode (unknown agent,
invalid state, suspended/revoked authority). It never fails open.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORIZE = ROOT / "tools" / "authorize.py"
STATE_DIR = ROOT / "contracts" / "trustops"

ACTIVE = STATE_DIR / "agent-authority-current-state.active.example.json"
REDUCED = STATE_DIR / "agent-authority-current-state.reduced.example.json"
SUSPENDED = STATE_DIR / "agent-authority-current-state.suspended.example.json"
REVOKED = STATE_DIR / "agent-authority-current-state.revoked.example.json"
RAW_RECEIPT = STATE_DIR / "agent-authority-current-state.raw-receipt.invalid.json"

AGENT = "agent-registry://agent-alpha"

EXIT_ALLOW = 0
EXIT_DENY = 1
EXIT_REVIEW = 3  # deliberately not 2 (argparse reserves 2 for usage errors)


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(AUTHORIZE), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, payload


def check(agent: str, action: str, *, state_file: Path | None = None, status: str | None = None):
    args = ["check", agent, "--action", action]
    if state_file is not None:
        args += ["--state-file", str(state_file)]
    if status is not None:
        args += ["--status", status]
    return run(*args)


# ---- allow only for resolvable, valid, sufficiently-authorized state ----

def test_active_tool_access_allows() -> None:
    code, out = check(AGENT, "tool", state_file=ACTIVE)
    assert out["verdict"] == "allow"
    assert out["ok"] is True
    assert out["reason_code"] == "effect_unchanged"
    assert out["receipt_hash"].startswith("sha256:")
    assert code == EXIT_ALLOW


def test_reduced_state_unchanged_dimension_still_allows() -> None:
    # Overall status is reduced, but memoryAccess is unchanged -> allow per-dimension.
    code, out = check(AGENT, "memory", state_file=REDUCED)
    assert out["verdict"] == "allow"
    assert code == EXIT_ALLOW


# ---- require-review for constrained dimensions ----

def test_reduced_tool_access_requires_review() -> None:
    code, out = check(AGENT, "tool", state_file=REDUCED)
    assert out["verdict"] == "require-review"
    assert out["effect_value"] == "reduced"
    assert code == EXIT_REVIEW


def test_reduced_autonomous_requires_human_approval() -> None:
    code, out = check(AGENT, "autonomous", state_file=REDUCED)
    assert out["verdict"] == "require-review"
    assert out["effect_value"] == "require-human-approval"
    assert code == EXIT_REVIEW


def test_reduced_egress_restricted_requires_review() -> None:
    code, out = check(AGENT, "egress", state_file=REDUCED)
    assert out["verdict"] == "require-review"
    assert code == EXIT_REVIEW


# ---- deny for every failure mode (fail closed) ----

def test_suspended_authority_denies_every_action() -> None:
    for action in ("tool", "memory", "autonomous", "route", "egress"):
        code, out = check(AGENT, action, state_file=SUSPENDED)
        assert out["verdict"] == "deny", action
        assert out["reason_code"] == "authority_status_suspended"
        assert code == EXIT_DENY


def test_revoked_authority_denies_every_action() -> None:
    for action in ("tool", "memory", "autonomous", "route", "egress"):
        code, out = check(AGENT, action, state_file=REVOKED)
        assert out["verdict"] == "deny", action
        assert out["reason_code"] == "authority_status_revoked"
        assert code == EXIT_DENY


def test_invalid_raw_receipt_state_denies_not_allows() -> None:
    # A record that is not a valid AgentAuthorityCurrentState must never authorize.
    code, out = check(AGENT, "tool", state_file=RAW_RECEIPT)
    assert out["verdict"] == "deny"
    assert out["ok"] is False
    assert out["reason_code"] == "authority_state_invalid"
    assert code == EXIT_DENY


def test_unknown_agent_denies() -> None:
    code, out = check("agent-registry://does-not-exist", "tool")
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "authority_state_not_found"
    assert code == EXIT_DENY


def test_agent_ref_mismatch_denies() -> None:
    # State file resolves to agent-alpha; requesting for a different agent must deny.
    code, out = check("agent-registry://agent-beta", "tool", state_file=ACTIVE)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "authority_state_agent_mismatch"
    assert code == EXIT_DENY


def test_ambiguous_state_denies() -> None:
    # Source-dir scan finds multiple states for agent-alpha (active/reduced/...) -> deny.
    code, out = check(AGENT, "tool")
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "authority_state_ambiguous"
    assert code == EXIT_DENY


def test_unknown_action_denies() -> None:
    code, out = check(AGENT, "launch-missiles", state_file=ACTIVE)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "unknown_action"
    assert code == EXIT_DENY


def test_argparse_usage_error_does_not_collide_with_review() -> None:
    # A parse error must exit with argparse's own code (2), never the semantic
    # require-review code (3) — so wrappers can't misread usage errors as a verdict.
    proc = subprocess.run(
        [sys.executable, str(AUTHORIZE), "check", AGENT],  # missing required --action
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 2
    assert proc.returncode != EXIT_REVIEW
