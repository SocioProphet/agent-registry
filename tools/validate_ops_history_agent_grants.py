#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples" / "ops-history"
REQUIRED_KEYS = {
    "grantId",
    "specVersion",
    "agentId",
    "grantFamily",
    "allowedEventClasses",
    "allowedPayloadModes",
    "scope",
    "endpointNames",
    "constraints",
    "policyDecisionRefs",
    "evidenceRefs",
    "expiresAt",
}
ALLOWED_PAYLOAD_MODES = {"metadata-only", "summary", "ref-only"}


def validate_file(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_KEYS - set(data))
    if missing:
        raise ValueError(f"{path}: missing keys {missing}")
    if data["grantFamily"] != "ops_history":
        raise ValueError(f"{path}: grantFamily must be ops_history")
    if not data["grantId"].startswith("urn:srcos:agent-grant:"):
        raise ValueError(f"{path}: grantId must use urn:srcos:agent-grant:")
    if not data["agentId"].startswith("urn:srcos:agent:"):
        raise ValueError(f"{path}: agentId must use urn:srcos:agent:")
    if not set(data["allowedPayloadModes"]).issubset(ALLOWED_PAYLOAD_MODES):
        raise ValueError(f"{path}: unsupported payload mode")
    if not data["allowedEventClasses"]:
        raise ValueError(f"{path}: allowedEventClasses must be non-empty")
    if not data["endpointNames"]:
        raise ValueError(f"{path}: endpointNames must be non-empty")
    constraints = data["constraints"]
    if constraints.get("dryRunOnly") is not True:
        raise ValueError(f"{path}: initial examples must be dryRunOnly")
    if constraints.get("humanBrowserProfileAllowed") is not False:
        raise ValueError(f"{path}: humanBrowserProfileAllowed must default false")
    return path.name


def main() -> int:
    files = sorted(EXAMPLE_DIR.glob("*.json"))
    if not files:
        raise SystemExit("No OpsHistory agent grant examples found")
    checked = [validate_file(path) for path in files]
    print(json.dumps({"ok": True, "checked": checked}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
