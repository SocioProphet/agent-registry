# TrustOps Agent Authority Current State v0.1

## Purpose

`AgentAuthorityCurrentState` records the current runtime authority posture for an agent.

It is derived from explicit authority decisions and restoration decisions. It is not inferred directly from raw TrustOps receipts.

This closes the control-plane gap between receipt evidence and runtime authority state.

## Boundary

Agent Registry owns:

- current authority state
- authority restoration decisions
- authority effect summaries
- restoration requirements

Guardrail Fabric owns TrustOps runtime action mapping.

AgentPlane consumes current authority state during attempt admission.

## Receipt evidence versus authority decision

The registry keeps the TrustOps receipt outcome separate from the governed authority decision.

A TrustOps receipt records what happened at a trust or safety gate:

```text
pass | warn | require-review | quarantine | block | rollback | revoke
```

An authority decision records what the registry decided to do to runtime authority:

```text
unchanged | reduced | suspended | revoked
```

Those fields must not collapse into a generic success flag. A high-uncertainty `require-review` receipt is not equivalent to a hard tool-abuse `revoke` receipt, and neither is itself the current authority state. The decision carries its own actor, policy, evidence, gate refs, `effective_at`, and restoration posture.

## Authority-decision semantic rules

The validator enforces the following receipt-to-authority bounds:

| TrustOps receipt outcome | Required authority posture |
|---|---|
| `pass` | `unchanged` only |
| `warn` | at most `reduced` |
| `require-review` | exactly `reduced` with `autonomousExecution=require-human-approval` |
| `quarantine` | exactly `suspended` |
| `block` | exactly `suspended` |
| `rollback` | exactly `suspended` |
| `revoke` | exactly `revoked` |

Additional effect rules:

- `authority_decision=unchanged` requires all `authorityEffects` to remain `unchanged`.
- Non-unchanged authority decisions require at least one changed authority effect.
- `quarantine`, `block`, and `rollback` suspend autonomous execution and block egress.
- `revoke` revokes tool access, memory access, autonomous execution, and route eligibility, and blocks egress.
- Any non-unchanged authority decision requires authorization evidence refs.

These rules preserve the audit seam: receipt as evidence, authority change as governed decision.

## Current state

The current-state record includes:

- `agentRef`
- `authority_status = active | reduced | suspended | revoked`
- `effective_decision_ref`
- `source_decision_refs`
- `evidenceRefs`
- `authorityEffects`
- `restoration_required`
- optional restoration policy and conditions

## Derivation rule

Current authority state must derive from one of:

- `trustops-agent-authority-decision:*`
- `authority-restoration-decision:*`

It must not derive directly from:

- `trustops-receipt:*`

Raw receipts are evidence. They are not authority mutations.

## Restoration

`AuthorityRestorationDecision` records explicit restoration or denial.

A passing TrustOps receipt does not automatically restore authority.

Restoration requires:

- a prior state ref
- a restoration decision
- an authorized decision actor
- authorization policy
- authorization evidence
- restored authority effects
- effective timestamp

## Validation

```bash
make validate-authority-state-contracts
make validate-trustops-agent-authority-decision
```

The validator checks:

- active/reduced/suspended/revoked current-state fixtures
- restoration decision fixture
- missing restoration authorization negative fixture
- raw-receipt-derived current-state negative fixture
- TrustOps authority-decision receipt/authority separation
- invalid pass-to-revoked authority escalation
- invalid require-review-with-unchanged authority
- invalid revoke-with-only-reduced authority

## Non-goals

This contract does not execute agent work.

It does not run safety preflight.

It does not emit AgentPlane attempt admissions.

It gives AgentPlane one authoritative authority-state input for admission decisions.
