#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    "agent-spec.example.json",
    "tool-grant.example.json",
    "session-authority.example.json",
    "revocation-record.example.json",
]
REQUIRED_AGENT_SPEC = {"ownerRef", "allowedSurfaceRefs", "toolGrantRefs", "memoryPolicyRef", "sessionPolicyRef", "evidenceRef", "revocationRef"}
REQUIRED_TOOL_GRANT = {"agentId", "toolRef", "scope", "constraints", "expiresAt", "evidenceRef"}
REQUIRED_SESSION = {"agentId", "activeToolGrantRefs", "activeSurfaceRefs", "sessionPolicyRef", "memoryPolicyRef", "evidenceRef", "status"}
REQUIRED_REVOCATION = {"agentId", "revokedToolGrantRefs", "revokedSurfaceRefs", "status", "reasonCodes", "evidenceRef"}
ALLOWED_AGENT_KINDS = {"codex", "copilot", "human", "local-cli", "system"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def require_fields(path: Path, spec: dict, required: set[str]) -> int:
    missing = sorted(required - set(spec))
    if missing:
        return fail(f"{path.name}: missing spec fields {missing}")
    return 0


def validate_record(path: Path) -> int:
    doc = load(path)
    if doc.get("apiVersion") != "agentregistry.socioprophet.dev/v1":
        return fail(f"{path.name}: apiVersion invalid")
    kind = doc.get("kind")
    metadata = doc.get("metadata", {})
    spec = doc.get("spec", {})
    if kind == "AgentSpec":
        if not metadata.get("agentId") or metadata.get("agentKind") not in ALLOWED_AGENT_KINDS:
            return fail(f"{path.name}: metadata.agentId and valid agentKind required")
        rc = require_fields(path, spec, REQUIRED_AGENT_SPEC)
        if rc:
            return rc
        if not spec["allowedSurfaceRefs"] or not spec["toolGrantRefs"]:
            return fail(f"{path.name}: allowedSurfaceRefs and toolGrantRefs must be non-empty")
    elif kind == "ToolGrant":
        if not metadata.get("grantId"):
            return fail(f"{path.name}: grantId required")
        rc = require_fields(path, spec, REQUIRED_TOOL_GRANT)
        if rc:
            return rc
        if not spec["constraints"]:
            return fail(f"{path.name}: constraints must be non-empty")
    elif kind == "SessionAuthority":
        if not metadata.get("sessionId"):
            return fail(f"{path.name}: sessionId required")
        rc = require_fields(path, spec, REQUIRED_SESSION)
        if rc:
            return rc
        if spec["status"] not in {"active", "expired", "revoked"}:
            return fail(f"{path.name}: session status invalid")
    elif kind == "RevocationRecord":
        if not metadata.get("revocationId"):
            return fail(f"{path.name}: revocationId required")
        rc = require_fields(path, spec, REQUIRED_REVOCATION)
        if rc:
            return rc
        if spec["status"] not in {"not-revoked", "revoked"}:
            return fail(f"{path.name}: revocation status invalid")
    else:
        return fail(f"{path.name}: unknown kind {kind}")
    return 0


def main() -> int:
    for name in EXAMPLES:
        rc = validate_record(ROOT / "examples" / name)
        if rc:
            return rc
    print(f"OK: validated {len(EXAMPLES)} agent registry examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
