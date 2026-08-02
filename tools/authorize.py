#!/usr/bin/env python3
"""AgentAuthorityAuthorize — fail-closed authorize decision surface.

This is the callable resolve/authorize surface that runtime consumers (e.g.
`agent-machine`, SourceOS-Linux#119) call before taking an action. Given an
agent identity and a requested action dimension, it resolves the agent's
validated AgentAuthorityCurrentState (reusing the read-only
authority_state_lookup helper) and returns an allow / require-review / deny
decision plus a hashed receipt.

INV-ACC-1 (Standard 030, "no invisible authority") is enforced HERE at runtime
as the FIRST gate, not just in CI. Before any authority state is read, the agent
must resolve to a registry admission entry (agents/admissions/) that is
admitted+granted; this surface calls the same fail-closed admission gate that CI
runs (`fail_closed_admission_gate.resolve_admission_for_ref`). A capability-
bearing agent with no resolvable admission entry is denied with reason
`invisible_authority_no_admission_entry`; a `proposed` (visible-but-unsigned)
entry is held at require-review and never authorizes.

It is fail-closed by construction:
  * capability-bearing agent with no admission entry -> deny (INV-ACC-1)
  * unknown agent, missing state, invalid state, or ambiguous state -> deny
  * suspended or revoked authority_status -> deny regardless of dimension
  * any authorityEffect value it does not explicitly recognize -> deny

Exit codes: 0 = allow, 3 = require-review, 1 = deny/error. 2 is deliberately
unused so it stays distinct from argparse's usage-error exit code.

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
import containment
import fail_closed_admission_gate as admission

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "contracts" / "trustops"
DEFAULT_ADMISSIONS_DIR = ROOT / "agents" / "admissions"
DEFAULT_GOVERNANCE_DIR = containment.DEFAULT_GOVERNANCE_DIR
DESTRUCTIVE_RISK_CLASS = "destructive-offensive"

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
# NOTE: 2 is intentionally avoided — argparse exits 2 on usage/parse errors, so
# reserving it keeps a parse error from being misread as an authorization verdict.
EXIT_ALLOW = 0
EXIT_DENY = 1
EXIT_REVIEW = 3


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
    admission: dict[str, Any] | None = None,
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
    payload = {
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
    # INV-ACC-1 admission is the first gate; surface its verdict on every
    # decision so a consumer can see the agent was (or was not) admitted.
    if admission is not None:
        payload["admission"] = admission
    return payload


def _admission_summary(decision: dict[str, Any]) -> dict[str, Any]:
    """Compact, runtime-facing view of an admission gate decision."""
    return {
        "invariant": "INV-ACC-1",
        "standard_ref": "socioprophet-agent-standards/docs/standards/030",
        "verdict": decision.get("verdict"),
        "reason_code": decision.get("reason_code"),
        "admission_status": decision.get("admission_status"),
        "authority_granted": decision.get("authority_granted"),
        "authority_refs": list(decision.get("authority_refs", [])),
    }


def authorize(
    agent_ref: str,
    action: str,
    *,
    source_dir: Path,
    state_file: str | None = None,
    status: str | None = None,
    admissions_dir: Path = DEFAULT_ADMISSIONS_DIR,
    governance_dir: Path = DEFAULT_GOVERNANCE_DIR,
    context: dict[str, Any] | None = None,
    enforce_admission: bool = True,
) -> dict[str, Any]:
    """Resolve current authority state and return an authorize decision.

    Fail-closed: any resolution failure yields a `deny` decision, never allow.

    INV-ACC-1 (Standard 030) is enforced HERE, at runtime, as the first gate:
    before any authority state is consulted, the agent MUST resolve to a
    registry admission entry that is admitted+granted. A capability-bearing
    agent with no resolvable admission entry is DENIED with reason
    `invisible_authority_no_admission_entry` -- no invisible authority. A
    `proposed` (visible-but-unsigned) entry never authorizes; it is held at
    require-review. Only after admission does the authorityEffects state govern
    the specific action dimension.
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

    # ---- Gate 1: INV-ACC-1 admission (no invisible authority) -------------- #
    admission_view: dict[str, Any] | None = None
    if enforce_admission:
        adm = admission.resolve_admission_for_ref(
            agent_ref, Path(admissions_dir), Path(governance_dir)
        )
        admission_view = _admission_summary(adm)
        if adm["verdict"] != "admitted":
            # Not admitted -> the agent has no runtime authority to evaluate.
            # deny -> deny; proposed/review-required -> require-review (visible
            # but never auto-authorized). Fail closed either way.
            authz_verdict = "deny" if adm["verdict"] == "deny" else "require-review"
            return _decision(
                verdict=authz_verdict,
                reason_code=adm["reason_code"],
                agent_ref=agent_ref,
                action=action,
                effect_key=ACTION_EFFECT[action],
                effect_value=None,
                authority_status=None,
                evidence_refs=list(adm.get("authority_refs", [])),
                source_state_hash=None,
                admission=admission_view,
            )

        # ---- Gate 1.5: CONTAINMENT for the destructive/offensive class ------ #
        # An admitted destructive/offensive agent is authorized ONLY when its
        # containment ref resolves to a REAL policy file AND that policy's
        # conditions are satisfied by the action context (deny-by-default).
        # This is what makes admission "governed, not omnipotent": a nominal
        # containment string cannot pass, and a satisfied real policy must.
        manifest = admission.load_manifest_for_ref(agent_ref, Path(admissions_dir))
        if manifest is not None and manifest.get("risk_class") == DESTRUCTIVE_RISK_CLASS:
            crefs = containment.containment_refs(manifest)
            cdecision = containment.gate(crefs, context or {}, Path(governance_dir))
            admission_view["containment"] = {
                "required": True,
                "allowed": cdecision["allowed"],
                "reason_code": cdecision["reason_code"],
                "resolved_policies": cdecision["resolved_policies"],
                "unmet": cdecision["unmet"],
            }
            if not cdecision["allowed"]:
                return _decision(
                    verdict="deny",
                    reason_code=cdecision["reason_code"],
                    agent_ref=agent_ref,
                    action=action,
                    effect_key=ACTION_EFFECT[action],
                    effect_value=None,
                    authority_status=None,
                    evidence_refs=list(adm.get("authority_refs", [])),
                    source_state_hash=None,
                    admission=admission_view,
                )

    # ---- Gate 2: authority state governs the specific action dimension ----- #
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
            admission=admission_view,
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
            admission=admission_view,
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
            admission=admission_view,
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
        admission=admission_view,
    )


def _context_from_args(args: argparse.Namespace) -> dict[str, Any]:
    """Build the action context that containment conditions are evaluated against.

    Deny-by-default: any flag left unset is absent from the context, so a policy
    that requires it treats it as UNMET.
    """
    context: dict[str, Any] = {}
    if args.env is not None:
        context["environment"] = args.env
    if args.sandbox:
        context["sandbox"] = True
    if args.human_in_loop:
        context["human_in_loop"] = True
    if args.read_only:
        context["read_only"] = True
    if args.quorum_approvers is not None:
        context["quorum_approvers"] = args.quorum_approvers
    if args.namespace_scope is not None:
        context["namespace_scope"] = args.namespace_scope
    return context


def command_authorize(args: argparse.Namespace) -> int:
    decision = authorize(
        args.agent_ref,
        args.action,
        source_dir=Path(args.source_dir),
        state_file=args.state_file,
        status=args.status,
        admissions_dir=Path(args.admissions_dir),
        governance_dir=Path(args.governance_dir),
        context=_context_from_args(args),
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
    authz.add_argument(
        "--admissions-dir",
        default=str(DEFAULT_ADMISSIONS_DIR),
        help="Registry admission directory (agents/admissions). INV-ACC-1 is "
        "always enforced by this surface: an agent with no resolvable, granted "
        "admission entry here is denied. There is deliberately no bypass flag.",
    )
    authz.add_argument(
        "--governance-dir",
        default=str(DEFAULT_GOVERNANCE_DIR),
        help="Governance root (containment/ + owner-signoffs/). For the "
        "destructive/offensive class, the named containment policy must resolve "
        "here AND its conditions must be satisfied, or the action is denied.",
    )
    # ---- action context the containment conditions are evaluated against ---- #
    authz.add_argument("--env", help="Execution environment (e.g. dev/staging/sandbox/prod).")
    authz.add_argument("--sandbox", action="store_true", help="Action runs inside an isolated sandbox.")
    authz.add_argument("--human-in-loop", action="store_true", help="A human is in the approval loop.")
    authz.add_argument("--read-only", action="store_true", help="Action is read-only (no mutation).")
    authz.add_argument("--quorum-approvers", type=int, help="Number of approvers in the quorum.")
    authz.add_argument("--namespace-scope", help="Namespace reach of the action (e.g. single/cross).")
    authz.set_defaults(func=command_authorize)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
