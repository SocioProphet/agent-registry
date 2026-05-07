#!/usr/bin/env python3
"""Validate Superconscious reasoning grant examples.

This validator is dependency-free and read-only. It checks the deterministic M1
agent grant posture: active demo agent, read-only mock tool, basic planner skill,
no model provider calls, prompt egress denied, memory proposal-only, and no
revocation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "superconscious-reasoning-grant.example.json"
REQUIRED_CONSTRAINTS = {
    "evidence-required",
    "safe-operational-trace-only",
    "no-network-egress",
    "no-host-state-change",
    "no-model-provider-call",
}


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(doc: dict[str, Any]) -> int:
    if doc.get("apiVersion") != "agentregistry.socioprophet.dev/v1":
        return fail("apiVersion invalid")
    if doc.get("kind") != "SuperconsciousReasoningGrant":
        return fail("kind must be SuperconsciousReasoningGrant")

    metadata = doc.get("metadata") or {}
    spec = doc.get("spec") or {}
    if not str(metadata.get("grantId", "")).startswith("urn:socioprophet:agent-grant:"):
        return fail("metadata.grantId must be an agent-grant URN")
    for key in [
        "reasoningRunRef",
        "agentId",
        "agentRole",
        "sessionRef",
        "workspaceRef",
        "status",
        "toolGrants",
        "skillGrants",
        "modelGrants",
        "memoryGrants",
        "constraints",
        "revocation",
        "evidenceRef",
    ]:
        if key not in spec:
            return fail(f"missing spec.{key}")

    if not str(spec["reasoningRunRef"]).startswith("urn:srcos:reasoning-run:"):
        return fail("reasoningRunRef must be a SourceOS reasoning-run URN")
    if not str(spec["agentId"]).startswith("urn:socioprophet:agent:"):
        return fail("agentId must be a SocioProphet agent URN")
    if not str(spec["sessionRef"]).startswith("urn:srcos:session:"):
        return fail("sessionRef must be a SourceOS session URN")
    if not str(spec["workspaceRef"]).startswith("urn:socioprophet:workspace:"):
        return fail("workspaceRef must be a SocioProphet workspace URN")
    if spec["status"] != "active":
        return fail("status must be active for deterministic M1 fixture")

    tool_grants = spec["toolGrants"]
    if not isinstance(tool_grants, list) or len(tool_grants) != 1:
        return fail("toolGrants must contain one mock read-only tool grant")
    tool = tool_grants[0]
    if tool.get("scope") != "readonly-mock" or tool.get("sideEffects") != "none" or tool.get("network") != "none":
        return fail("tool grant must be readonly-mock with no side effects and no network")

    skill_grants = spec["skillGrants"]
    if not isinstance(skill_grants, list) or not skill_grants:
        return fail("skillGrants must be non-empty")
    if skill_grants[0].get("scope") != "deterministic-local":
        return fail("basic planner skill must be deterministic-local")

    model_grants = spec["modelGrants"]
    if not isinstance(model_grants, list) or len(model_grants) != 1:
        return fail("modelGrants must contain one deterministic stub route")
    model = model_grants[0]
    if model.get("providerClass") != "none" or model.get("modelCalls") != "none" or model.get("promptEgress") != "denied":
        return fail("model grant must deny provider calls and prompt egress")

    memory_grants = spec["memoryGrants"]
    if not isinstance(memory_grants, list) or len(memory_grants) != 1:
        return fail("memoryGrants must contain one proposal-only grant")
    memory = memory_grants[0]
    if memory.get("memoryScope") != "proposal-only" or memory.get("durableWrite") is not False:
        return fail("memory grant must be proposal-only with durableWrite=false")

    constraints = set(spec["constraints"])
    if not REQUIRED_CONSTRAINTS.issubset(constraints):
        return fail("constraints missing required deterministic M1 constraints")
    revocation = spec["revocation"]
    if revocation.get("status") != "not-revoked":
        return fail("revocation.status must be not-revoked")
    if not str(spec["evidenceRef"]).startswith("urn:srcos:reasoning-event:"):
        return fail("evidenceRef must reference a SourceOS reasoning event")

    print("OK: Superconscious reasoning grant example validated")
    return 0


def main() -> int:
    return validate(load(FIXTURE))


if __name__ == "__main__":
    raise SystemExit(main())
