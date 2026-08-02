"""Runtime containment-enforcement tests (INV-ACC-1, Standard 030).

These prove containment is a REAL teeth, not a nominal string: the callable
authorize surface (`tools/authorize.py`) authorizes a destructive/offensive
agent ONLY when (a) its named `policy://containment/...` ref resolves to a real
policy file AND (b) that policy's conditions are satisfied by the action
context. Otherwise it DENIES, deny-by-default.

Two agent populations are exercised:
  * a hermetic fixture agent (contained-agent) with a full authority state, so
    the SATISFIED path reaches an end-to-end allow;
  * the REAL priority admissions (governor-001 kill.agent, scope-exploit), whose
    real containment policies deny prod and pass a satisfied sandbox context
    (proving containment is not the blocker) before the per-action authority
    state governs.

References: SocioProphet/agent-registry#53/#54/#55, Standard 030 INV-ACC-1.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHORIZE = ROOT / "tools" / "authorize.py"

# Real estate under test.
REAL_ADMISSIONS = ROOT / "agents" / "admissions"
REAL_GOVERNANCE = ROOT / "governance"

# Hermetic fixture estate.
FIX = Path(__file__).resolve().parent / "fixtures" / "containment"
FIX_ADMISSIONS = FIX / "admissions"
FIX_GOVERNANCE = FIX / "governance"
FIX_STATE = FIX / "states" / "contained-agent.active.json"
CONTAINED = "agent-registry://contained-agent"

EXIT_ALLOW = 0
EXIT_DENY = 1
EXIT_REVIEW = 3


def check(agent: str, action: str, *flags: str, admissions_dir: Path, governance_dir: Path,
          state_file: Path | None = None) -> tuple[int, dict]:
    argv = [
        sys.executable, str(AUTHORIZE), "check", agent,
        "--action", action,
        "--admissions-dir", str(admissions_dir),
        "--governance-dir", str(governance_dir),
    ]
    if state_file is not None:
        argv += ["--state-file", str(state_file)]
    argv += list(flags)
    proc = subprocess.run(argv, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, payload


SATISFIED = ("--env", "sandbox", "--sandbox", "--human-in-loop", "--namespace-scope", "single")


# ---- hermetic: satisfied real containment -> end-to-end ALLOW ---------------

def test_contained_agent_allowed_when_containment_resolves_and_satisfied() -> None:
    code, out = check(CONTAINED, "tool", *SATISFIED,
                      admissions_dir=FIX_ADMISSIONS, governance_dir=FIX_GOVERNANCE,
                      state_file=FIX_STATE)
    assert out["admission"]["verdict"] == "admitted"
    assert out["admission"]["containment"]["allowed"] is True
    assert out["admission"]["containment"]["reason_code"] == "containment_satisfied"
    assert out["admission"]["containment"]["resolved_policies"] == [
        "policy://containment/test-contain-sandbox-v0.1"
    ]
    assert out["verdict"] == "allow"
    assert code == EXIT_ALLOW


# ---- hermetic: conditions UNMET (prod) -> DENY ------------------------------

def test_contained_agent_denied_when_conditions_unmet() -> None:
    code, out = check(CONTAINED, "tool", "--env", "prod", "--namespace-scope", "single",
                      admissions_dir=FIX_ADMISSIONS, governance_dir=FIX_GOVERNANCE,
                      state_file=FIX_STATE)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "containment_conditions_unmet"
    assert out["admission"]["containment"]["allowed"] is False
    # prod is explicitly denied and sandbox/human-in-loop are unmet.
    unmet = out["admission"]["containment"]["unmet"]
    assert any("environment_denied:prod" in u for u in unmet)
    assert any("sandbox_required" in u for u in unmet)
    assert code == EXIT_DENY


# ---- hermetic: containment policy ABSENT -> DENY (fail-closed) --------------

def test_contained_agent_denied_when_containment_policy_absent(tmp_path: Path) -> None:
    empty_gov = tmp_path / "governance"
    (empty_gov / "containment").mkdir(parents=True)
    code, out = check(CONTAINED, "tool", *SATISFIED,
                      admissions_dir=FIX_ADMISSIONS, governance_dir=empty_gov,
                      state_file=FIX_STATE)
    assert out["verdict"] == "deny"
    # No policy file -> admission gate itself fail-closes before conditions.
    assert out["reason_code"] in {"containment_policy_unresolved", "invisible_authority_no_admission_entry"}
    assert code == EXIT_DENY


# ---- REAL priority admissions: governor-001 (kill.agent) --------------------

def test_real_governor_denied_in_prod_by_real_containment() -> None:
    # kill.agent in prod: the REAL containment policy denies it (prod excluded,
    # sandbox/human-in-loop/quorum unmet) -> deny containment_conditions_unmet.
    code, out = check("agent:governor-001", "autonomous", "--env", "prod",
                      admissions_dir=REAL_ADMISSIONS, governance_dir=REAL_GOVERNANCE)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "containment_conditions_unmet"
    assert out["admission"]["containment"]["allowed"] is False
    assert code == EXIT_DENY


def test_real_governor_containment_satisfied_then_authority_state_governs() -> None:
    # Satisfy the REAL kill.agent containment policy (staging + sandbox +
    # human-in-loop + quorum>=2 + single namespace). Containment is then NOT the
    # blocker; the per-action authority state governs (none on file -> deny with
    # an authority-state reason, NOT a containment reason). This proves the
    # containment ref is real and passable, and that admission != omnipotence.
    code, out = check("agent:governor-001", "autonomous",
                      "--env", "staging", "--sandbox", "--human-in-loop",
                      "--quorum-approvers", "2", "--namespace-scope", "single",
                      admissions_dir=REAL_ADMISSIONS, governance_dir=REAL_GOVERNANCE)
    assert out["admission"]["verdict"] == "admitted"
    assert out["admission"]["containment"]["allowed"] is True
    assert out["admission"]["containment"]["reason_code"] == "containment_satisfied"
    assert not out["reason_code"].startswith("containment_")
    assert out["reason_code"] == "authority_state_not_found"
    assert out["verdict"] == "deny"


# ---- REAL priority admissions: scope-exploit --------------------------------

def test_real_exploit_denied_without_sandbox() -> None:
    # scope-exploit requires an isolated sandbox + human-in-loop; a bare context
    # (no sandbox) is denied by the real exploit containment policy.
    code, out = check("scope-exploit", "tool", "--env", "sandbox",
                      admissions_dir=REAL_ADMISSIONS, governance_dir=REAL_GOVERNANCE)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "containment_conditions_unmet"
    assert any("human_in_loop_required" in u for u in out["admission"]["containment"]["unmet"])
    assert code == EXIT_DENY
