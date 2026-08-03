#!/usr/bin/env python3
"""Containment resolution + fail-closed evaluation (INV-ACC-1, Standard 030).

A destructive/offensive admission carries a ``policy://containment/<name>`` ref.
This module turns that ref into REAL enforcement, not a nominal string:

  * ``policy_file_exists`` / ``load_policy`` resolve the ref to a real file at
    ``governance/containment/<name>.json``. A ref that does not resolve to a
    real, well-formed ContainmentPolicy is an UNRESOLVED containment -> fail
    closed (the caller denies).
  * ``evaluate`` checks the policy's ``required_conditions`` against the action
    context, deny-by-default: every present condition must be satisfied and a
    missing context value for a present condition is treated as UNMET.
  * ``gate`` composes the two: given the containment refs on a manifest and an
    action context, it returns allow only when EVERY ref resolves to a real
    policy AND every policy is satisfied.

This is what makes "contained" mean contained instead of a string that says so.
It does not grant credentials, mutate authority, or run the action.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOVERNANCE_DIR = ROOT / "governance"

CONTAINMENT_SCHEME = "policy://containment/"
CONTAINMENT_RECORD_TYPE = "ContainmentPolicy"
EVIDENCE_SIGNOFF_SCHEME = "evidence://agent-registry/owner-signoff/"


class ContainmentError(Exception):
    """Unresolvable / malformed containment. Always maps to a deny."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


# --------------------------------------------------------------------------- #
# Ref resolution                                                              #
# --------------------------------------------------------------------------- #

def containment_ref_to_path(ref: str, governance_dir: Path = DEFAULT_GOVERNANCE_DIR) -> Path | None:
    if not isinstance(ref, str) or not ref.startswith(CONTAINMENT_SCHEME):
        return None
    name = ref[len(CONTAINMENT_SCHEME):]
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return None  # reject traversal / nested names
    return governance_dir / "containment" / f"{name}.json"


def signoff_ref_to_path(ref: str, governance_dir: Path = DEFAULT_GOVERNANCE_DIR) -> Path | None:
    if not isinstance(ref, str) or not ref.startswith(EVIDENCE_SIGNOFF_SCHEME):
        return None
    name = ref[len(EVIDENCE_SIGNOFF_SCHEME):]
    if not name or "/" in name or "\\" in name or name.startswith("."):
        return None
    return governance_dir / "owner-signoffs" / f"{name}.json"


def policy_file_exists(ref: str, governance_dir: Path = DEFAULT_GOVERNANCE_DIR) -> bool:
    path = containment_ref_to_path(ref, governance_dir)
    return bool(path and path.is_file())


def signoff_file_exists(ref: str, governance_dir: Path = DEFAULT_GOVERNANCE_DIR) -> bool:
    path = signoff_ref_to_path(ref, governance_dir)
    return bool(path and path.is_file())


def load_policy(ref: str, governance_dir: Path = DEFAULT_GOVERNANCE_DIR) -> dict[str, Any]:
    path = containment_ref_to_path(ref, governance_dir)
    if path is None:
        raise ContainmentError("containment_ref_malformed", f"not a containment ref: {ref!r}")
    if not path.is_file():
        raise ContainmentError("containment_policy_unresolved", f"no containment policy file for {ref} ({path})")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContainmentError("containment_policy_invalid_json", f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(record, dict) or record.get("recordType") != CONTAINMENT_RECORD_TYPE:
        raise ContainmentError("containment_policy_malformed", f"{path.name}: not a {CONTAINMENT_RECORD_TYPE}")
    if record.get("policy_ref") != ref:
        raise ContainmentError(
            "containment_policy_ref_mismatch",
            f"{path.name}: policy_ref {record.get('policy_ref')!r} != {ref!r}",
        )
    return record


def containment_refs(manifest: dict[str, Any]) -> list[str]:
    """All containment refs a manifest names (authority_refs + sign_off), deduped."""
    refs: list[str] = []
    for ref in manifest.get("authority", {}).get("authority_refs", []):
        if isinstance(ref, str) and ref.startswith(CONTAINMENT_SCHEME) and ref not in refs:
            refs.append(ref)
    sign_off = manifest.get("authority", {}).get("sign_off") or {}
    cref = sign_off.get("containment_ref")
    if isinstance(cref, str) and cref.startswith(CONTAINMENT_SCHEME) and cref not in refs:
        refs.append(cref)
    return refs


# --------------------------------------------------------------------------- #
# Condition evaluation (deny-by-default)                                       #
# --------------------------------------------------------------------------- #

def evaluate(policy: dict[str, Any], context: dict[str, Any]) -> list[str]:
    """Return the list of UNMET condition reasons. Empty list == satisfied.

    Deny-by-default: a present required condition whose context value is missing
    or false is UNMET. Extra context is ignored.
    """
    unmet: list[str] = []
    rc = policy.get("required_conditions", {}) or {}
    denied_envs = policy.get("denied_environments", []) or []
    env = context.get("environment")

    if env in denied_envs:
        unmet.append(f"environment_denied:{env}")

    if "environment_in" in rc:
        allowed = rc["environment_in"]
        if env is None:
            unmet.append("environment_missing")
        elif env not in allowed:
            unmet.append(f"environment_not_allowed:{env}")

    if rc.get("require_sandbox") and context.get("sandbox") is not True:
        unmet.append("sandbox_required")
    if rc.get("require_human_in_loop") and context.get("human_in_loop") is not True:
        unmet.append("human_in_loop_required")
    if rc.get("require_read_only") and context.get("read_only") is not True:
        unmet.append("read_only_required")

    if "min_quorum_approvers" in rc:
        approvers = context.get("quorum_approvers")
        if not isinstance(approvers, int) or approvers < rc["min_quorum_approvers"]:
            unmet.append(f"quorum_below_min:{rc['min_quorum_approvers']}")

    if "namespace_scope_in" in rc:
        scope = context.get("namespace_scope")
        if scope is None:
            unmet.append("namespace_scope_missing")
        elif scope not in rc["namespace_scope_in"]:
            unmet.append(f"namespace_scope_not_allowed:{scope}")

    return unmet


# --------------------------------------------------------------------------- #
# Composite gate                                                               #
# --------------------------------------------------------------------------- #

def gate(
    refs: list[str],
    context: dict[str, Any],
    governance_dir: Path = DEFAULT_GOVERNANCE_DIR,
) -> dict[str, Any]:
    """Fail-closed containment decision for a destructive/offensive agent.

    allow only if there is >=1 containment ref, EVERY ref resolves to a real
    ContainmentPolicy, and EVERY policy is satisfied by the context. Otherwise
    deny with a specific reason_code.
    """
    if not refs:
        return {
            "allowed": False,
            "reason_code": "destructive_without_containment_ref",
            "resolved_policies": [],
            "unmet": ["no_containment_ref"],
        }

    resolved: list[str] = []
    for ref in refs:
        try:
            policy = load_policy(ref, governance_dir)
        except ContainmentError as exc:
            return {
                "allowed": False,
                "reason_code": exc.reason_code,
                "resolved_policies": resolved,
                "unmet": [f"{ref}:{exc.reason_code}"],
            }
        unmet = evaluate(policy, context)
        if unmet:
            return {
                "allowed": False,
                "reason_code": "containment_conditions_unmet",
                "resolved_policies": resolved + [ref],
                "unmet": [f"{ref}:{reason}" for reason in unmet],
            }
        resolved.append(ref)

    return {
        "allowed": True,
        "reason_code": "containment_satisfied",
        "resolved_policies": resolved,
        "unmet": [],
    }
