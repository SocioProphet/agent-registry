#!/usr/bin/env python3
"""Validate WorkspaceContextAuthorityBinding example."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "contracts/workspace-context/workspace-context-authority-binding.v0.1.schema.json"
EXAMPLE = ROOT / "contracts/workspace-context/workspace-context-authority-binding.v0.1.example.json"


def main():
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        for key in schema["required"]:
            if key not in example:
                raise AssertionError(f"missing {key}")
        assert example["schemaVersion"] == "agent-registry.workspace-context-authority-binding.v0.1"
        assert example["recordType"] == "WorkspaceContextAuthorityBinding"
        assert example["workroomRef"].startswith("workroom://")
        assert example["contextGraphRef"]
        assert example["runtimeBindingRef"]
        assert example["agentRefs"]
        assert example["sessionRefs"]
        assert example["authorityStateRefs"]
        assert example["grantRefs"]
        assert example["policyRefs"]
        assert example["evidenceRefs"]
    except Exception as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2
    print("OK: WorkspaceContextAuthorityBinding validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
