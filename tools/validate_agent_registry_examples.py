#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
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
REQUIRED_AGENT_SPEC = {"ownerRef", "allowedSurfaceRefs", "toolGrantRefs", "memoryPolicyRef", "sessionPolicyRef", "evidenceRef", "revocationRef"}
REQUIRED_TOOL_GRANT = {"agentId", "toolRef", "scope", "constraints", "expiresAt", "evidenceRef"}
REQUIRED_SESSION = {"agentId", "activeToolGrantRefs", "activeSurfaceRefs", "sessionPolicyRef", "memoryPolicyRef", "evidenceRef", "status"}
REQUIRED_REVOCATION = {"agentId", "revokedToolGrantRefs", "revokedSurfaceRefs", "status", "reasonCodes", "evidenceRef"}
ALLOWED_AGENT_KINDS = {"codex", "copilot", "human", "local-cli", "system"}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def require_fields(label: str, spec: dict, required: set[str]) -> int:
    missing = sorted(required - set(spec))
    if missing:
        return fail(f"{label}: missing spec fields {missing}")
    return 0


def record_label(path: Path, index: int | None = None) -> str:
    rel = path.relative_to(ROOT)
    if index is None:
        return str(rel)
    return f"{rel}[{index}]"


def validate_record(doc: dict[str, Any], label: str) -> int:
    if doc.get("apiVersion") != "agentregistry.socioprophet.dev/v1":
        return fail(f"{label}: apiVersion invalid")
    kind = doc.get("kind")
    metadata = doc.get("metadata", {})
    spec = doc.get("spec", {})
    if kind == "AgentSpec":
        if not metadata.get("agentId") or metadata.get("agentKind") not in ALLOWED_AGENT_KINDS:
            return fail(f"{label}: metadata.agentId and valid agentKind required")
        rc = require_fields(label, spec, REQUIRED_AGENT_SPEC)
        if rc:
            return rc
        if not spec["allowedSurfaceRefs"] or not spec["toolGrantRefs"]:
            return fail(f"{label}: allowedSurfaceRefs and toolGrantRefs must be non-empty")
    elif kind == "ToolGrant":
        if not metadata.get("grantId"):
            return fail(f"{label}: grantId required")
        rc = require_fields(label, spec, REQUIRED_TOOL_GRANT)
        if rc:
            return rc
        if not spec["constraints"]:
            return fail(f"{label}: constraints must be non-empty")
        if "evidence-required" not in set(spec["constraints"]):
            return fail(f"{label}: evidence-required constraint is mandatory")
    elif kind == "SessionAuthority":
        if not metadata.get("sessionId"):
            return fail(f"{label}: sessionId required")
        rc = require_fields(label, spec, REQUIRED_SESSION)
        if rc:
            return rc
        if spec["status"] not in {"active", "expired", "revoked"}:
            return fail(f"{label}: session status invalid")
    elif kind == "RevocationRecord":
        if not metadata.get("revocationId"):
            return fail(f"{label}: revocationId required")
        rc = require_fields(label, spec, REQUIRED_REVOCATION)
        if rc:
            return rc
        if spec["status"] not in {"not-revoked", "revoked"}:
            return fail(f"{label}: revocation status invalid")
    else:
        return fail(f"{label}: unknown kind {kind}")
    return 0


def iter_records(path: Path):
    doc = load(path)
    if isinstance(doc, list):
        for index, record in enumerate(doc):
            yield record, record_label(path, index)
    else:
        yield doc, record_label(path)


def validate_professional_intelligence_cross_refs() -> int:
    base = ROOT / "examples" / "professional-intelligence"
    agents = load(base / "agent-specs.example.json")
    grants = load(base / "tool-grants.example.json")
    session = load(base / "session-authority.example.json")
    revocation = load(base / "revocation-record.example.json")

    grant_ids = {grant["metadata"]["grantId"] for grant in grants}
    agent_ids = {agent["metadata"]["agentId"] for agent in agents}

    for agent in agents:
        for grant_ref in agent["spec"]["toolGrantRefs"]:
            if grant_ref not in grant_ids:
                return fail(f"professional-intelligence: agent references missing grant {grant_ref}")

    for grant in grants:
        agent_id = grant["spec"]["agentId"]
        if agent_id not in agent_ids:
            return fail(f"professional-intelligence: grant references missing agent {agent_id}")

    session_spec = session["spec"]
    if session_spec["agentId"] not in agent_ids:
        return fail("professional-intelligence: session references missing agent")
    for grant_ref in session_spec["activeToolGrantRefs"]:
        if grant_ref not in grant_ids:
            return fail(f"professional-intelligence: session references missing grant {grant_ref}")

    if revocation["spec"]["agentId"] not in agent_ids:
        return fail("professional-intelligence: revocation references missing agent")

    return 0


def main() -> int:
    count = 0
    for path in EXAMPLES:
        for record, label in iter_records(path):
            rc = validate_record(record, label)
            if rc:
                return rc
            count += 1

    rc = validate_professional_intelligence_cross_refs()
    if rc:
        return rc

    print(f"OK: validated {count} agent registry examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
