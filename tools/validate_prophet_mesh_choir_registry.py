#!/usr/bin/env python3
"""Validate the Prophet Mesh choir registry mirror fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "contracts/prophet-mesh/prophet-mesh-choir-registry.v0.1.json"

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "kind",
    "source_repo",
    "source_contracts",
    "release_channel",
    "default_conductor",
    "required_controls",
    "required_default_agents",
    "agents",
    "non_claims",
}
REQUIRED_AGENT_FIELDS = {
    "id",
    "kind",
    "label",
    "status",
    "version",
    "role",
    "capabilities",
    "allowed_memory_scopes",
    "required_controls",
}
REQUIRED_CONTROLS = {"identity", "policy", "evidence", "audit"}
ALLOWED_KINDS = {"conductor", "specialist"}
ALLOWED_STATUSES = {"active", "reduced", "suspended", "revoked"}
FORBIDDEN_MEMORY_SCOPES = {"unscoped", "all", "unrestricted", "raw_memory", "private_unapproved"}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("fixture must be a JSON object")
    return data


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_TOP_LEVEL - set(data)
    if missing:
        errors.append("missing top-level fields: " + ", ".join(sorted(missing)))

    if data.get("kind") != "prophet_mesh_choir_registry_mirror":
        errors.append("kind must be prophet_mesh_choir_registry_mirror")
    if data.get("source_repo") != "SocioProphet/prophet-mesh":
        errors.append("source_repo must be SocioProphet/prophet-mesh")
    if data.get("release_channel") != "private_preview":
        errors.append("release_channel must be private_preview")
    if data.get("default_conductor") != "michael-agent":
        errors.append("default_conductor must be michael-agent")

    if not _is_non_empty_list(data.get("source_contracts")):
        errors.append("source_contracts must be a non-empty list")
    if not _is_non_empty_list(data.get("non_claims")):
        errors.append("non_claims must be a non-empty list")
    else:
        non_claims_text = " ".join(str(item).lower() for item in data["non_claims"])
        for phrase in ["does not grant live credentials", "does not execute runtime tasks", "does not certify production autonomy"]:
            if not all(word in non_claims_text for word in phrase.split()):
                errors.append(f"non_claims missing boundary: {phrase}")

    required_controls = {str(item) for item in data.get("required_controls", [])}
    missing_controls = REQUIRED_CONTROLS - required_controls
    if missing_controls:
        errors.append("required_controls missing: " + ", ".join(sorted(missing_controls)))

    agents = data.get("agents", [])
    if not _is_non_empty_list(agents):
        errors.append("agents must be a non-empty list")
        return errors

    by_id: dict[str, dict[str, Any]] = {}
    for index, agent in enumerate(agents):
        if not isinstance(agent, dict):
            errors.append(f"agents[{index}] must be an object")
            continue
        missing_agent_fields = REQUIRED_AGENT_FIELDS - set(agent)
        if missing_agent_fields:
            errors.append(f"agents[{index}] missing fields: " + ", ".join(sorted(missing_agent_fields)))
        agent_id = agent.get("id")
        if not _is_non_empty_string(agent_id):
            errors.append(f"agents[{index}].id must be a non-empty string")
            continue
        if agent_id in by_id:
            errors.append(f"duplicate agent id: {agent_id}")
        by_id[str(agent_id)] = agent

        if agent.get("kind") not in ALLOWED_KINDS:
            errors.append(f"agents[{index}].kind must be conductor or specialist")
        if agent.get("status") not in ALLOWED_STATUSES:
            errors.append(f"agents[{index}].status must be active, reduced, suspended, or revoked")
        if not _is_non_empty_list(agent.get("capabilities")):
            errors.append(f"agents[{index}].capabilities must be a non-empty list")
        scopes = {str(item) for item in agent.get("allowed_memory_scopes", []) if isinstance(item, str)}
        if not scopes:
            errors.append(f"agents[{index}].allowed_memory_scopes must be a non-empty list")
        forbidden = FORBIDDEN_MEMORY_SCOPES & scopes
        if forbidden:
            errors.append(f"agents[{index}] includes forbidden memory scopes: " + ", ".join(sorted(forbidden)))
        controls = {str(item) for item in agent.get("required_controls", []) if isinstance(item, str)}
        missing_agent_controls = REQUIRED_CONTROLS - controls
        if missing_agent_controls:
            errors.append(f"agents[{index}] missing required controls: " + ", ".join(sorted(missing_agent_controls)))

    required_default_agents = {str(item) for item in data.get("required_default_agents", [])}
    if not required_default_agents:
        errors.append("required_default_agents must be a non-empty list")
    for agent_id in sorted(required_default_agents):
        if agent_id not in by_id:
            errors.append(f"required default agent missing from agents: {agent_id}")
        elif by_id[agent_id].get("status") != "active":
            errors.append(f"required default agent must be active: {agent_id}")

    conductor = by_id.get(str(data.get("default_conductor")))
    if conductor is None:
        errors.append("default conductor missing from agents")
    elif conductor.get("kind") != "conductor":
        errors.append("default conductor must be kind conductor")

    specialist_count = sum(1 for agent in by_id.values() if agent.get("kind") == "specialist")
    if specialist_count < 2:
        errors.append("registry mirror must contain at least two specialist agents")

    return errors


def main() -> int:
    try:
        data = _load_json(FIXTURE)
    except Exception as exc:  # pragma: no cover - defensive CLI path
        print(f"ERR: failed to load {FIXTURE}: {exc}", file=sys.stderr)
        return 2

    errors = validate(data)
    report = {
        "validator": "agent-registry.prophet-mesh-choir-registry.validator.v1",
        "passed": not errors,
        "problems": errors,
        "fixture": str(FIXTURE.relative_to(ROOT)),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    print(("PASS" if not errors else "FAIL") + ": Prophet Mesh choir registry mirror")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
