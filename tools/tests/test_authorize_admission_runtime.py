"""Runtime INV-ACC-1 enforcement tests for the authorize surface (Standard 030).

These prove *teeth at runtime*, not in CI: the callable authorize surface
(`tools/authorize.py`), which runtime consumers invoke before taking an action,
DENIES a capability-bearing agent that has no resolvable, granted registry
admission entry -- even when that agent presents a perfectly valid, active
AgentAuthorityCurrentState. Before this wiring the admission gate
(`fail_closed_admission_gate.py`) ran only under `make validate` / pytest over
fixture files; the runtime authorize path never consulted it, so an agent with
authority state but no admission entry ("invisible authority") was authorized.

References: SocioProphet/agent-registry#53 (gap), #54 (the CI admission gate),
socioprophet-agent-standards Standard 030, invariant INV-ACC-1.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
AUTHORIZE = TOOLS / "authorize.py"

FIX = Path(__file__).resolve().parent / "fixtures" / "admission-runtime"
ADMISSIONS = FIX / "admissions"
STATES = FIX / "states"

GOOD_STATE = STATES / "good-agent.active.json"
DANGER_STATE = STATES / "danger-agent.active.json"
GHOST_STATE = STATES / "ghost-agent.active.json"

GOOD = "agent-registry://good-agent"
DANGER = "agent-registry://danger-agent"
GHOST = "agent-registry://ghost-agent"

EXIT_ALLOW = 0
EXIT_DENY = 1
EXIT_REVIEW = 3  # deliberately not 2 (argparse reserves 2 for usage errors)


def check(agent: str, action: str, *, state_file: Path, admissions_dir: Path = ADMISSIONS) -> tuple[int, dict]:
    proc = subprocess.run(
        [
            sys.executable,
            str(AUTHORIZE),
            "check",
            agent,
            "--action",
            action,
            "--state-file",
            str(state_file),
            "--admissions-dir",
            str(admissions_dir),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, payload


# ---- (a) admitted agent + valid state -> authorized ------------------------

def test_admitted_agent_with_active_state_is_authorized() -> None:
    code, out = check(GOOD, "tool", state_file=GOOD_STATE)
    assert out["verdict"] == "allow"
    assert out["ok"] is True
    assert out["admission"]["verdict"] == "admitted"
    assert out["admission"]["invariant"] == "INV-ACC-1"
    assert code == EXIT_ALLOW


# ---- (b) THE TEETH: valid active state but NO admission entry -> DENIED -----

def test_valid_active_state_without_admission_entry_is_denied() -> None:
    # ghost-agent has a fully valid, active AgentAuthorityCurrentState with all
    # authorityEffects unchanged -- Gate 2 alone would ALLOW it. There is no
    # admission entry, so Gate 1 (INV-ACC-1) denies it at runtime.
    code, out = check(GHOST, "tool", state_file=GHOST_STATE)
    assert out["verdict"] == "deny"
    assert out["ok"] is False
    assert out["reason_code"] == "invisible_authority_no_admission_entry"
    assert out["admission"]["verdict"] == "deny"
    # Proof that admission is the FIRST gate: authority state was never consulted.
    assert out["authority_status"] is None
    assert out["source_state_hash"] is None
    assert code == EXIT_DENY


# ---- (c) PRIORITY: a proposed destructive agent is never runtime-authorized -

def test_proposed_kill_agent_is_never_authorized_at_runtime() -> None:
    # danger-agent declares kill.agent and HAS a valid active authority state,
    # but its admission is only `proposed` (visible, authority.granted=false).
    # The runtime surface must hold it at require-review, never allow.
    code, out = check(DANGER, "autonomous", state_file=DANGER_STATE)
    assert out["verdict"] != "allow"
    assert out["verdict"] == "require-review"
    assert out["reason_code"] == "proposed_admission_pending_owner_sign_off"
    assert out["admission"]["verdict"] == "review-required"
    assert out["admission"]["admission_status"] == "proposed"
    assert out["admission"]["authority_granted"] is False
    assert code == EXIT_REVIEW


def test_destructive_verb_absent_admission_is_denied(tmp_path: Path) -> None:
    # Same destructive agent, but pointed at an EMPTY admissions dir: not even a
    # proposed stub resolves -> the kill.agent bearer is denied outright.
    empty = tmp_path / "admissions"
    empty.mkdir()
    code, out = check(DANGER, "autonomous", state_file=DANGER_STATE, admissions_dir=empty)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "invisible_authority_no_admission_entry"
    assert code == EXIT_DENY


# ---- fail-closed substrate -------------------------------------------------

def test_empty_admissions_dir_denies_admitted_fixture(tmp_path: Path) -> None:
    # Even the admitted good-agent is denied when the admissions substrate is
    # empty/unreadable: the gate fails closed, never open.
    empty = tmp_path / "admissions"
    empty.mkdir()
    code, out = check(GOOD, "tool", state_file=GOOD_STATE, admissions_dir=empty)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "invisible_authority_no_admission_entry"
    assert code == EXIT_DENY


# ---- contrast: what the runtime gate now prevents --------------------------

def test_without_enforcement_the_invisible_agent_would_have_been_allowed() -> None:
    # Import the surface directly to exercise the enforce_admission=False path.
    # This documents exactly the pre-remediation hole: with admission NOT
    # enforced, ghost-agent's valid active state authorizes it. The CLI has NO
    # bypass flag, so this weakened mode is unreachable at runtime.
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    import authorize as authorize_mod

    enforced = authorize_mod.authorize(
        GHOST, "tool", source_dir=STATES, state_file=str(GHOST_STATE), admissions_dir=ADMISSIONS
    )
    assert enforced["verdict"] == "deny"
    assert enforced["reason_code"] == "invisible_authority_no_admission_entry"

    bypassed = authorize_mod.authorize(
        GHOST,
        "tool",
        source_dir=STATES,
        state_file=str(GHOST_STATE),
        admissions_dir=ADMISSIONS,
        enforce_admission=False,
    )
    assert bypassed["verdict"] == "allow"  # exactly the invisible authority the runtime gate now blocks
