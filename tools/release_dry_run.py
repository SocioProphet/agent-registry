#!/usr/bin/env python3
"""Release dry-run: emits deterministic local metadata under dist/.

Collects all agent registry example records, bundles them into a single
manifest artifact in dist/, and writes a SHA-256 checksum alongside it.

This is a DRY-RUN only.
  - No artifact is published to any release channel.
  - No Homebrew formula URL or checksum is generated for production use.
  - No credentials, tokens, or secrets are used.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

DRY_RUN_VERSION = "0.0.0-dry-run"

EXAMPLES = [
    ROOT / "examples" / "agent-spec.example.json",
    ROOT / "examples" / "tool-grant.example.json",
    ROOT / "examples" / "session-authority.example.json",
    ROOT / "examples" / "revocation-record.example.json",
    ROOT / "examples" / "professional-intelligence" / "agent-specs.example.json",
    ROOT / "examples" / "professional-intelligence" / "tool-grants.example.json",
    ROOT / "examples" / "professional-intelligence" / "session-authority.example.json",
    ROOT / "examples" / "professional-intelligence" / "revocation-record.example.json",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_records() -> list[dict[str, Any]]:
    """Return a flat list of all agent registry records from the example files."""
    records: list[dict[str, Any]] = []
    for path in EXAMPLES:
        doc = load(path)
        if isinstance(doc, list):
            records.extend(doc)
        else:
            records.append(doc)
    return records


def build_manifest(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "apiVersion": "agentregistry.socioprophet.dev/v1",
        "kind": "ReleaseDryRunManifest",
        "metadata": {
            "version": DRY_RUN_VERSION,
            "note": (
                "dry-run only — not a stable release; "
                "no Homebrew URL or checksum here is valid for production use"
            ),
        },
        "records": records,
    }


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)

    records = collect_records()
    manifest = build_manifest(records)

    artifact_name = f"agent-registry-{DRY_RUN_VERSION}.json"
    artifact_path = DIST / artifact_name
    checksum_path = DIST / f"{artifact_name}.sha256"

    # Serialize deterministically: sorted keys, consistent indentation, UTF-8
    artifact_bytes = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")

    artifact_path.write_bytes(artifact_bytes)
    digest = sha256_of(artifact_bytes)
    checksum_path.write_text(f"{digest}  {artifact_name}\n", encoding="utf-8")

    print(f"dist: {artifact_path.relative_to(ROOT)}")
    print(f"sha256: {checksum_path.relative_to(ROOT)}")
    print(f"digest: {digest}")
    print("OK: release dry-run complete — no production release published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
