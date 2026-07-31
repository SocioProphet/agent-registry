# Agent Authority Authorize (v0.1)

`tools/authorize.py` is the callable, fail-closed **authorize decision surface**
for Agent Registry. It answers one question for a runtime consumer:

> May agent `X` take action of dimension `A` right now?

It returns an `allow` / `require-review` / `deny` decision plus a hash-bound
receipt. It is the seam that `agent-machine`
([SourceOS-Linux#119](https://github.com/SourceOS-Linux/agent-machine/issues/119))
calls before acting, and is part of the Integration Mission epic
([SocioProphet/socioprophet#490](https://github.com/SocioProphet/socioprophet/issues/490)).

## What it does

1. Resolves the agent's validated `AgentAuthorityCurrentState` using the
   read-only `authority_state_lookup` helper (same validation, same
   fail-closed loading — it never derives authority from raw receipts).
2. Maps the requested `--action` to the governing `authorityEffects` key:

   | action        | authorityEffects key   |
   | ------------- | ---------------------- |
   | `tool`        | `toolAccess`           |
   | `memory`      | `memoryAccess`         |
   | `autonomous`  | `autonomousExecution`  |
   | `route`       | `routeEligibility`     |
   | `egress`      | `egressMode`           |

3. Produces a verdict:

   | effect value                              | verdict          |
   | ----------------------------------------- | ---------------- |
   | `unchanged`                               | `allow`          |
   | `reduced` / `require-human-approval` / `restricted` | `require-review` |
   | `suspended` / `revoked` / `blocked`       | `deny`           |
   | anything unrecognized                     | `deny`           |

A `suspended` or `revoked` `authority_status` denies **every** action
regardless of the per-dimension effect (global gate).

## Fail-closed guarantees

The surface only returns `allow` for a resolvable, valid, sufficiently-
authorized state. Every failure mode denies — it never fails open:

- unknown agent / no matching state → `deny` (`authority_state_not_found`)
- ambiguous state (multiple matches) → `deny` (`authority_state_ambiguous`)
- invalid state record (e.g. a raw receipt) → `deny` (`authority_state_invalid`)
- agent / status mismatch on an explicit `--state-file` → `deny`
- unrecognized action dimension → `deny` (`unknown_action`)

Exit codes are fail-closed for shell/CI gating: `0` = allow, `2` =
require-review, `1` = deny or error. Only a clean allow exits `0`.

## Usage

```bash
# Resolve from the local contracts/trustops source dir (must be unambiguous):
python3 tools/authorize.py check agent-registry://agent-alpha --action tool --status active

# Or against an explicit state file:
python3 tools/authorize.py check agent-registry://agent-alpha --action autonomous \
  --state-file contracts/trustops/agent-authority-current-state.reduced.example.json
```

The emitted `AgentAuthorityAuthorizeDecision` carries a `receipt_hash`
(sha256 over the decision core), the `source_state_hash` of the state it
read, and the `evidenceRefs` carried forward — so a decision is a verifiable
artifact, not just an exit code.

## Boundary

Authorize records a decision over recorded authority state. It does **not**
mutate authority, approve restoration, derive state from raw receipts, issue
live credentials, perform AgentPlane admission, or execute anything. Those
remain with their respective authorities (TrustOps, Guardrail Fabric,
AgentPlane, Model Governance Ledger, Prophet Platform).

## Validate

```bash
make validate-agent-authority-authorize
python3 -m pytest -q tools/tests/test_authorize.py
```
