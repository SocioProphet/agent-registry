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
```

The validator checks:

- active/reduced/suspended/revoked current-state fixtures
- restoration decision fixture
- missing restoration authorization negative fixture
- raw-receipt-derived current-state negative fixture

## Non-goals

This contract does not execute agent work.

It does not run safety preflight.

It does not emit AgentPlane attempt admissions.

It gives AgentPlane one authoritative authority-state input for admission decisions.
