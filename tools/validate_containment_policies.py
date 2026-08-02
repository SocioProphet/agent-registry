#!/usr/bin/env python3
"""Validate the governance substrate for admissions (INV-ACC-1, Standard 030).

Proves the admissions' evidence and containment refs are REAL, not nominal:

  1. Every governance/containment/*.json validates against the ContainmentPolicy
     schema, and its policy_ref matches its filename.
  2. The owner sign-off record validates against the OwnerSignOffRecord schema.
  3. Every admitted destructive/offensive admission manifest names >=1
     containment ref, and every containment ref it names RESOLVES to a real
     policy file (round-trip).
  4. Every admission sign_off.evidence_ref (owner sign-off) RESOLVES to a real
     record file.

Fail-closed: any missing/mismatched/malformed artifact is an error (exit 1). A
green run means "contained/approved" points at real, governed objects.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import containment
from fail_closed_admission_gate import GateError, _validate_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
GOVERNANCE = ROOT / "governance"
ADMISSIONS = ROOT / "agents" / "admissions"

CONTAINMENT_SCHEMA = SCHEMAS / "containment-policy.v0.1.schema.json"
SIGNOFF_SCHEMA = SCHEMAS / "owner-signoff.v0.1.schema.json"
DESTRUCTIVE = "destructive-offensive"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []

    # 1. Containment policies validate + filename matches policy_ref.
    cschema = _load(CONTAINMENT_SCHEMA)
    for path in sorted((GOVERNANCE / "containment").glob("*.json")):
        rec = _load(path)
        try:
            _validate_schema(cschema, rec, path.name)
        except GateError as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        expected_ref = f"policy://containment/{path.stem}"
        if rec.get("policy_ref") != expected_ref:
            errors.append(f"{path.name}: policy_ref {rec.get('policy_ref')!r} != {expected_ref!r}")

    # 2. Owner sign-off record(s) validate.
    sschema = _load(SIGNOFF_SCHEMA)
    for path in sorted((GOVERNANCE / "owner-signoffs").glob("*.json")):
        try:
            _validate_schema(sschema, _load(path), path.name)
        except GateError as exc:
            errors.append(f"{path.name}: {exc}")

    # 3 + 4. Every admitted destructive/offensive manifest's containment +
    # evidence refs round-trip to real files.
    checked = 0
    for path in sorted(ADMISSIONS.glob("*.admission.json")):
        rec = _load(path)
        if rec.get("admission_status") != "admitted":
            continue
        if rec.get("risk_class") != DESTRUCTIVE:
            continue
        checked += 1
        crefs = containment.containment_refs(rec)
        if not crefs:
            errors.append(f"{path.name}: admitted destructive/offensive agent names NO containment ref")
        for cref in crefs:
            if not containment.policy_file_exists(cref, GOVERNANCE):
                errors.append(f"{path.name}: containment ref {cref} does not resolve to a real policy file")
        sign_off = rec.get("authority", {}).get("sign_off") or {}
        eref = sign_off.get("evidence_ref")
        if not eref or not containment.signoff_file_exists(eref, GOVERNANCE):
            errors.append(f"{path.name}: sign_off evidence_ref {eref!r} does not resolve to a real record file")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"OK: governance substrate valid; {checked} admitted destructive/offensive admissions fully warranted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
