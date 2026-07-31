#!/usr/bin/env python3
"""AgentAuthorityAuthorize — fail-closed authorize decision surface.

This is the callable resolve/authorize surface that runtime consumers (e.g.
`agent-machine`, SourceOS-Linux#119) call before taking an action. Given an
agent identity and a requested action dimension, it resolves the agent's
validated AgentAuthorityCurrentState (reusing the read-only
authority_state_lookup helper) and returns an allow / require-review / deny
decision plus a hashed receipt.

It is fail-closed by construction:
  * unknown agent, missing state, invalid state, or ambiguous state -> deny
  * suspended or revoked authority_status -> deny regardless of dimension
  * any authorityEffect value it does not explicitly recognize -> deny

It does not mutate authority, derive state from raw receipts, grant live
credentials, or replace runtime/model/policy/guardrail/AgentPlane authorities.
Those boundaries are inherited from authority_state_lookup and the TrustOps
contracts this surface reads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import authority_state_lookup as lookup

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "contracts" / "trustops"

NON_GOALS = [
    "authority_mutation",
    "restoration_approval",
    "raw_receipt_to_authority_state_derivation",
    "live_credential_issuance",
    "agentplane_admission",
    "runtime_execution",
]

# Requested action dimension -> the authorityEffects key that governs it.
ACTION_EFFECT = {
    "tool": "toolAccess",
    "memory": "memoryAccess",
    "autonomous": "autonomousExecution",
    "route": "routeEligibility",
    "egress": "egressMode",
}

# authorityEffect values that hard-deny the requested action.
DENY_VALUES = {"suspended", "revoked", "blocked"}
# authorityEffect values that permit the action only under human review / constraint.
REVIEW_VALUES = {"reduced", "require-human-approval", "restricted"}
# authorityEffect values that cleanly allow the action.
ALLOW_VALUES = {"unchanged"}

# authority_status values that hard-deny every action regardless of dimension.
GLOBAL_DENY_STATUS = {"suspended", "revoked"}

# Exit codes are fail-closed for shell/CI gating: only a clean allow exits 0.
EXIT_ALLOW = 0
EXIT_DENY = 1
EXIT_REVIEW = 2


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _receipt_hash(core: dict[str, Any]) -> str:
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _verdict_for_effect(value: str) -> str:
    if value in DENY_VALUES:
        return "deny"
    if value in REVIEW_VALUES:
        return "require-review"
    if value in ALLOW_VALUES:
        return "allow"
    # Unrecognized effect value: fail closed.
    return "deny"


def _decision(
    *,
    verdict: str,
    reason_code: str,
    agent_ref: str,
    action: str,
    effect_key: str | None,
    effect_value: str | None,
    authority_status: str | None,
    evidence_refs: list[str],
    source_state_hash: str | None,
) -> dict[str, Any]:
    decided_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = {
        "agentRef": agent_ref,
        "action": action,
        "verdict": verdict,
        "authority_status": authority_status,
        "effect_key": effect_key,
        "effect_value": effect_value,
        "source_state_hash": source_state_hash,
        "decided_at": decided_at,
    }
    return {
        "schemaVersion": "agent-registry.agent-authority-authorize.v0.1",
        "recordType": "AgentAuthorityAuthorizeDecision",
        "ok": verdict == "allow",
        "mode": "readonly",
        "verdict": verdict,
        "reason_code": reason_code,
        "agentRef": agent_ref,
        "action": action,
        "authority_status": authority_status,
        "effect_key": effect_key,
        "effect_value": effect_value,
        "evidenceRefs": evidence_refs,
        "source_state_hash": source_state_hash,
        "decided_at": decided_at,
        "receipt_hash": _receipt_hash(core),
        "non_goals": NON_GOALS,
    }


def authorize(
    agent_ref: str,
    action: str,
    *,
    source_dir: Path,
    state_file: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Resolve current authority state and return an authorize decision.

    Fail-closed: any resolution failure yields a `deny` decision, never allow.
    """
    if action not in ACTION_EFFECT:
        return _decision(
            verdict="deny",
            reason_code="unknown_action",
            agent_ref=agent_ref,
            action=action,
            effect_key=None,
            effect_value=None,
            authority_status=None,
            evidence_refs=[],
            source_state_hash=None,
        )

    # Resolve validated current state via the read-only lookup helper.
    try:
        if state_file:
            record = lookup.load_validated_state(Path(state_file))
            if record.get("agentRef") != agent_ref:
                raise lookup.LookupError(
                    "authority_state_agent_mismatch",
                    f"state file agentRef {record.get('agentRef')} does not match requested {agent_ref}",
                )
            if status and record.get("authority_status") != status:
                raise lookup.LookupError(
                    "authority_state_status_mismatch",
                    f"state file status {record.get('authority_status')} does not match requested {status}",
                )
        else:
            record, _path = lookup.find_state(source_dir, agent_ref, status)
    except lookup.LookupError as exc:
        # No resolvable, valid authority state -> deny (fail closed).
        return _decision(
            verdict="deny",
            reason_code=exc.reason_code,
            agent_ref=agent_ref,
            action=action,
            effect_key=ACTION_EFFECT[action],
            effect_value=None,
            authority_status=None,
            evidence_refs=[],
            source_state_hash=None,
        )

    authority_status = record.get("authority_status")
    evidence_refs = list(record.get("evidenceRefs", []))
    source_state_hash = record.get("receipt_hash")
    effect_key = ACTION_EFFECT[action]

    # Global gate: suspended/revoked authority denies every action.
    if authority_status in GLOBAL_DENY_STATUS:
        return _decision(
            verdict="deny",
            reason_code=f"authority_status_{authority_status}",
            agent_ref=agent_ref,
            action=action,
            effect_key=effect_key,
            effect_value=record.get("authorityEffects", {}).get(effect_key),
            authority_status=authority_status,
            evidence_refs=evidence_refs,
            source_state_hash=source_state_hash,
        )

    effects = record.get("authorityEffects", {})
    if effect_key not in effects:
        # Contract guarantees this key, but never trust a missing field.
        return _decision(
            verdict="deny",
            reason_code="authority_effect_missing",
            agent_ref=agent_ref,
            action=action,
            effect_key=effect_key,
            effect_value=None,
            authority_status=authority_status,
            evidence_refs=evidence_refs,
            source_state_hash=source_state_hash,
        )

    effect_value = effects[effect_key]
    verdict = _verdict_for_effect(effect_value)
    reason_code = {
        "allow": "effect_unchanged",
        "require-review": f"effect_{effect_value}",
        "deny": f"effect_{effect_value}",
    }[verdict]

    return _decision(
        verdict=verdict,
        reason_code=reason_code,
        agent_ref=agent_ref,
        action=action,
        effect_key=effect_key,
        effect_value=effect_value,
        authority_status=authority_status,
        evidence_refs=evidence_refs,
        source_state_hash=source_state_hash,
    )


def command_authorize(args: argparse.Namespace) -> int:
    decision = authorize(
        args.agent_ref,
        args.action,
        source_dir=Path(args.source_dir),
        state_file=args.state_file,
        status=args.status,
    )
    emit(decision)
    return {"allow": EXIT_ALLOW, "require-review": EXIT_REVIEW, "deny": EXIT_DENY}[decision["verdict"]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-authority-authorize",
        description="Fail-closed authorize decision over AgentAuthorityCurrentState.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    authz = sub.add_parser("check", help="Authorize an agent action against current authority state.")
    authz.add_argument("agent_ref")
    authz.add_argument(
        "--action",
        required=True,
        help=f"Requested action dimension (one of: {', '.join(sorted(ACTION_EFFECT))}). "
        "An unrecognized action is denied by the surface, not rejected by the parser.",
    )
    authz.add_argument("--status", choices=["active", "reduced", "suspended", "revoked"])
    authz.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    authz.add_argument("--state-file")
    authz.set_defaults(func=command_authorize)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
