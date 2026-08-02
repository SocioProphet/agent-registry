"""Fail-closed admission gate tests (INV-ACC-1, Standard 030).

The property under test: the gate only ever returns `admitted` (exit 0) for an
agent whose declared capability resolves to an admission entry that is BOTH
admission_status=admitted AND authority.granted=true with non-empty
authority_refs. Every other case -- no admission entry (invisible authority),
proposed stub, denied/revoked entry, malformed input -- is held below admitted.
It never fails open.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "tools" / "fail_closed_admission_gate.py"
ADMISSIONS = ROOT / "agents" / "admissions"
DECLARED = ROOT / "examples" / "admission-gate" / "declared"
UNADMITTED = ROOT / "examples" / "admission-gate" / "unadmitted-capability-agent.invalid.json"

EXIT_ADMITTED = 0
EXIT_DENY = 1
EXIT_REVIEW = 3  # deliberately not 2 (argparse reserves 2 for usage errors)


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(GATE), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, payload


def check(declared_file: Path, admissions_dir: Path = ADMISSIONS) -> tuple[int, dict]:
    return run("check", str(declared_file), "--admissions-dir", str(admissions_dir))


# ---- admitted only for a resolvable, granted admission entry ---------------

def test_admitted_agent_passes() -> None:
    code, out = check(DECLARED / "example-admitted-agent.declared.json")
    assert out["verdict"] == "admitted"
    assert out["ok"] is True
    assert out["reason_code"] == "admitted_with_authority"
    assert out["authority_refs"]
    assert code == EXIT_ADMITTED


# ---- INV-ACC-1: capability without an admission entry is denied -------------

def test_capability_without_admission_entry_denies() -> None:
    code, out = check(UNADMITTED)
    assert out["verdict"] == "deny"
    assert out["ok"] is False
    assert out["reason_code"] == "invisible_authority_no_admission_entry"
    assert out["declared_capabilities"]  # it DID declare capability
    assert code == EXIT_DENY


# ---- owner-signed-off: the priority destructive/offensive subset is admitted -
# Lord Michael (owner) approved these 9 on 2026-08-02; each admission is now
# admitted+granted and carries a CONTAINMENT ref so approval is governed, not
# omnipotent (SocioProphet/agent-registry#53/#54/#55, Standard 030 INV-ACC-1).

@pytest.mark.parametrize(
    "stem",
    [
        "agent-governor-001",  # kill.agent / policy.evaluate / quorum.vote
        "agent-shell-001",  # exec.command / fs.write
        "scope-exploit",
        "scope-enum-iam",
        "scope-enum-kms",
        "scope-enum-secrets",
        "scope-enum-sts",
        "scope-attack-paths",
        "splunk-mcp-server",
    ],
)
def test_owner_approved_destructive_subset_is_admitted_and_contained(stem: str) -> None:
    code, out = check(DECLARED / f"{stem}.declared.json")
    assert out["verdict"] == "admitted"
    assert out["ok"] is True
    assert out["admission_status"] == "admitted"
    assert out["authority_granted"] is True
    assert out["reason_code"] == "admitted_with_authority"
    assert out["authority_refs"]  # warranting refs are populated on sign-off
    # governed, not omnipotent: a containment/policy ref must be present for the
    # destructive/offensive class so admission != unconditional authority.
    assert any(ref.startswith("policy://containment/") for ref in out["authority_refs"])
    # the owner sign-off evidence is recorded among the warranting refs.
    assert (
        "evidence://agent-registry/owner-signoff/2026-08-02-lord-michael-approval"
        in out["authority_refs"]
    )
    assert code == EXIT_ADMITTED


# ---- fail-closed on every malformed / unresolvable input -------------------

def test_unknown_agent_with_empty_admissions_denies(tmp_path: Path) -> None:
    empty = tmp_path / "admissions"
    empty.mkdir()
    code, out = check(DECLARED / "agent-governor-001.declared.json", admissions_dir=empty)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "invisible_authority_no_admission_entry"
    assert code == EXIT_DENY


def test_admitted_entry_without_authority_refs_denies(tmp_path: Path) -> None:
    # An admission that claims admitted+granted but carries NO authority_refs must
    # not pass: authority with no warrant is still invisible authority.
    admissions = tmp_path / "admissions"
    admissions.mkdir()
    (admissions / "x.admission.json").write_text(
        json.dumps(
            {
                "schemaVersion": "agent-registry.agent-admission-manifest.v0.1",
                "recordType": "AgentAdmissionManifest",
                "agent_id": "agent:x",
                "declared_capabilities": ["exec.command"],
                "admission_status": "admitted",
                "production_admitted": True,
                "authority": {
                    "granted": True,
                    "authority_refs": [],
                    "owner_repo": "SocioProphet/x",
                    "approval_required_from": "owner",
                    "sign_off": {"approver": "owner"},
                },
                "invariant": "INV-ACC-1",
                "standard_ref": "socioprophet-agent-standards/docs/standards/030",
                "gap_ref": "SocioProphet/agent-registry#53",
            }
        ),
        encoding="utf-8",
    )
    declared = tmp_path / "x.declared.json"
    declared.write_text(
        json.dumps(
            {
                "schemaVersion": "agent-registry.declared-capability-record.v0.1",
                "recordType": "DeclaredCapabilityRecord",
                "agent_id": "agent:x",
                "declared_capabilities": ["exec.command"],
            }
        ),
        encoding="utf-8",
    )
    code, out = check(declared, admissions_dir=admissions)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "admitted_without_authority_refs"
    assert code == EXIT_DENY


def test_duplicate_admission_entry_is_ambiguous_and_denies(tmp_path: Path) -> None:
    admissions = tmp_path / "admissions"
    admissions.mkdir()
    body = {
        "schemaVersion": "agent-registry.agent-admission-manifest.v0.1",
        "recordType": "AgentAdmissionManifest",
        "agent_id": "agent:dup",
        "declared_capabilities": ["exec.command"],
        "admission_status": "proposed",
        "production_admitted": False,
        "authority": {
            "granted": False,
            "authority_refs": [],
            "owner_repo": "SocioProphet/x",
            "approval_required_from": "owner",
            "sign_off": None,
        },
        "invariant": "INV-ACC-1",
        "standard_ref": "socioprophet-agent-standards/docs/standards/030",
        "gap_ref": "SocioProphet/agent-registry#53",
    }
    (admissions / "a.admission.json").write_text(json.dumps(body), encoding="utf-8")
    (admissions / "b.admission.json").write_text(json.dumps(body), encoding="utf-8")
    declared = tmp_path / "dup.declared.json"
    declared.write_text(
        json.dumps(
            {
                "schemaVersion": "agent-registry.declared-capability-record.v0.1",
                "recordType": "DeclaredCapabilityRecord",
                "agent_id": "agent:dup",
                "declared_capabilities": ["exec.command"],
            }
        ),
        encoding="utf-8",
    )
    code, out = check(declared, admissions_dir=admissions)
    assert out["verdict"] == "deny"
    assert out["reason_code"] == "admission_ambiguous"
    assert code == EXIT_DENY


def test_no_declared_capability_is_not_gated(tmp_path: Path) -> None:
    # An agent that declares no capability holds no authority to gate.
    declared = tmp_path / "empty.declared.json"
    declared.write_text(
        json.dumps(
            {
                "schemaVersion": "agent-registry.declared-capability-record.v0.1",
                "recordType": "DeclaredCapabilityRecord",
                "agent_id": "agent:no-caps",
                "declared_capabilities": [],
            }
        ),
        encoding="utf-8",
    )
    code, out = check(declared)
    assert out["verdict"] == "admitted"
    assert out["reason_code"] == "no_declared_capability"
    assert code == EXIT_ADMITTED


def test_scan_priority_population_is_admitted_after_owner_sign_off() -> None:
    # After the owner (Lord Michael, 2026-08-02) signed off, the whole priority
    # population (9 destructive/offensive agents + the benign example) resolves
    # to admitted; the aggregate is a clean admitted (exit 0). The fail-closed
    # teeth live in test_scan_denies_when_any_agent_has_no_admission below.
    code, out = run("scan", str(DECLARED), "--admissions-dir", str(ADMISSIONS))
    assert out["aggregate_verdict"] == "admitted"
    assert out["counts"]["denied"] == 0
    assert out["counts"]["review_required"] == 0
    assert out["counts"]["admitted"] == 10
    assert code == EXIT_ADMITTED


def test_scan_denies_when_any_agent_has_no_admission(tmp_path: Path) -> None:
    declared_dir = tmp_path / "declared"
    declared_dir.mkdir()
    # One agent with no admission entry -> whole scan denies (fail closed).
    (declared_dir / "ghost.json").write_text(
        json.dumps(
            {
                "schemaVersion": "agent-registry.declared-capability-record.v0.1",
                "recordType": "DeclaredCapabilityRecord",
                "agent_id": "agent:ghost",
                "declared_capabilities": ["kill.agent"],
            }
        ),
        encoding="utf-8",
    )
    code, out = run("scan", str(declared_dir), "--admissions-dir", str(ADMISSIONS))
    assert out["aggregate_verdict"] == "deny"
    assert code == EXIT_DENY


def test_scan_self_excludes_non_agent_files(tmp_path: Path) -> None:
    declared_dir = tmp_path / "declared"
    declared_dir.mkdir()
    # A non-DeclaredCapabilityRecord (e.g. an admission manifest dropped here)
    # must be skipped, not gated as an agent.
    (declared_dir / "substrate.json").write_text(
        json.dumps({"recordType": "AgentAdmissionManifest", "agent_id": "x"}),
        encoding="utf-8",
    )
    code, out = run("scan", str(declared_dir), "--admissions-dir", str(ADMISSIONS))
    assert out["counts"]["scanned"] == 0
    assert out["counts"]["skipped_non_agent_files"] == 1
    assert out["aggregate_verdict"] == "admitted"  # nothing to gate
    assert code == EXIT_ADMITTED


def test_argparse_usage_error_does_not_collide_with_review() -> None:
    proc = subprocess.run(
        [sys.executable, str(GATE), "check"],  # missing required declared_file
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 2
    assert proc.returncode != EXIT_REVIEW
