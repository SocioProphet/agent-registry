from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "release_dry_run.py"
DIST = ROOT / "dist"


def _run_dry_run():
    """Run release_dry_run.py and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_release_dry_run_exits_zero() -> None:
    result = _run_dry_run()
    assert result.returncode == 0, result.stderr + result.stdout


def test_release_dry_run_prints_ok() -> None:
    result = _run_dry_run()
    assert "OK: release dry-run complete" in result.stdout
    assert "no production release published" in result.stdout


def test_release_dry_run_emits_artifact() -> None:
    _run_dry_run()
    artifact = DIST / "agent-registry-0.0.0-dry-run.json"
    assert artifact.exists(), f"expected {artifact} to exist"


def test_release_dry_run_emits_checksum() -> None:
    _run_dry_run()
    checksum = DIST / "agent-registry-0.0.0-dry-run.json.sha256"
    assert checksum.exists(), f"expected {checksum} to exist"


def test_release_dry_run_checksum_matches_artifact() -> None:
    _run_dry_run()
    artifact = DIST / "agent-registry-0.0.0-dry-run.json"
    checksum_file = DIST / "agent-registry-0.0.0-dry-run.json.sha256"

    digest_line = checksum_file.read_text(encoding="utf-8").strip()
    expected_digest = digest_line.split()[0]

    actual_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert actual_digest == expected_digest


def test_release_dry_run_manifest_structure() -> None:
    _run_dry_run()
    artifact = DIST / "agent-registry-0.0.0-dry-run.json"
    manifest = json.loads(artifact.read_text(encoding="utf-8"))

    assert manifest["apiVersion"] == "agentregistry.socioprophet.dev/v1"
    assert manifest["kind"] == "ReleaseDryRunManifest"
    assert manifest["metadata"]["version"] == "0.0.0-dry-run"
    assert "records" in manifest
    assert len(manifest["records"]) > 0


def test_release_dry_run_manifest_contains_all_kinds() -> None:
    _run_dry_run()
    artifact = DIST / "agent-registry-0.0.0-dry-run.json"
    manifest = json.loads(artifact.read_text(encoding="utf-8"))

    kinds = {record["kind"] for record in manifest["records"]}
    assert "AgentSpec" in kinds
    assert "ToolGrant" in kinds
    assert "SessionAuthority" in kinds
    assert "RevocationRecord" in kinds


def test_release_dry_run_is_deterministic() -> None:
    """Running the script twice must produce identical output."""
    _run_dry_run()
    artifact = DIST / "agent-registry-0.0.0-dry-run.json"
    first_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    _run_dry_run()
    second_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    assert first_digest == second_digest


def test_release_dry_run_note_excludes_homebrew_production_claim() -> None:
    """The manifest note must not claim production Homebrew validity."""
    _run_dry_run()
    artifact = DIST / "agent-registry-0.0.0-dry-run.json"
    manifest = json.loads(artifact.read_text(encoding="utf-8"))

    note = manifest["metadata"]["note"].lower()
    assert "dry-run" in note
    assert "not a stable release" in note or "no homebrew url" in note.replace("-", " ")
