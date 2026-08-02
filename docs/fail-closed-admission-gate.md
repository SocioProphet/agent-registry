# Fail-Closed Admission Gate — INV-ACC-1 (no invisible authority)

Realizes invariant **INV-ACC-1** from `SocioProphet/socioprophet-agent-standards`
Standard 030 and closes `SocioProphet/agent-registry#53` (*invisible authority:
46 capability-bearing agents with no admission*).

> **INV-ACC-1.** An agent that declares capabilities MUST resolve to a registry
> admission entry. Capability without admission = **denied**.

## The gap

A read-only harvest of the estate (`prophet-core-catalog`
`datasets/agents-manifests/agents.jsonl`, `ds.agents-manifests`) found **46
agents** that declare capabilities (`declared_capabilities` non-empty) but trace
to **no** authority manifest (`authority_refs: []`) and have **no** registry
admission entry (`registry_ref: null`). The dangerous subset declares potent
verbs with no owner, grant, or policy behind them:

- `agent_descriptors` capability-decls — `policy.evaluate`, **`kill.agent`**,
  `quorum.vote` (governor), `exec.command` / `fs.write` (shell).
- SCOPE-D `claude-subagent`s — cloud enum/exploit subagents (IAM, KMS, Secrets,
  STS, exploit, attack-paths) holding `Bash`/`Write`/`WebFetch`.
- SCOPE-D / smart-tree `mcp-server`s — tool surfaces such as the Splunk MCP
  `cmd:bash`.

## The gate

`tools/fail_closed_admission_gate.py` enforces INV-ACC-1. It takes a
`DeclaredCapabilityRecord` (what an agent claims it can do) and resolves it
against the registry admission index (`agents/admissions/*.admission.json`,
schema `schemas/agent-admission-manifest.v0.1.schema.json`).

| Situation | Verdict | Exit |
|---|---|---|
| Resolvable admission entry, `admitted` + `authority.granted` + non-empty `authority_refs` | `admitted` | `0` |
| Resolvable admission entry, `proposed` | `review-required` | `3` |
| Admission entry `denied` / `revoked` | `deny` | `1` |
| **Capability declared, NO admission entry** | `deny` | `1` |
| Malformed / ambiguous / unknown status | `deny` | `1` |
| No declared capability | `admitted` (nothing to gate) | `0` |

It is **fail-closed**: only an explicit, resolvable, granted admission ever exits
`0`. Exit `2` is deliberately avoided so an argparse usage error can never be
misread as a verdict. It never mutates authority, signs off proposed stubs,
issues credentials, or replaces runtime/model/policy/guardrail/AgentPlane
authorities.

**Self-exclusion.** The gate governs *agents*. The registry substrate — this
checker, the admission manifests, the schema — is not a capability-bearing agent
under test. `scan` only ingests `DeclaredCapabilityRecord`s and skips everything
else (`skipped_non_agent_files`).

## Usage

```bash
# Gate one declared record:
python3 tools/fail_closed_admission_gate.py check <declared.json> [--admissions-dir agents/admissions]

# Gate a whole population (worst-case aggregate verdict):
python3 tools/fail_closed_admission_gate.py scan examples/admission-gate/declared
```

## Proposed stubs are NOT authorization

This PR scaffolds **proposed** admission stubs (`admission_status: proposed`,
`authority.granted: false`, `authority_refs: []`) for the priority
destructive/offensive subset. They make the invisible authority **visible** — so
the gate can hold them at `review-required` instead of denying them as unknown —
but they grant nothing. The schema forbids a proposed manifest from claiming
granted authority or production admission. Promotion to `admitted` is the owning
repo's decision (populate `authority_refs`, set `authority.sign_off`,
`authority.granted: true`, `admission_status: admitted`). See
`agents/admissions/README.md`.

## Validation

```bash
make validate-fail-closed-admission-gate      # stdlib-only; teeth both ways
python3 -m pytest -q tools/tests/test_fail_closed_admission_gate.py
```

`make validate` runs the gate target in the aggregate validation chain; CI is
`.github/workflows/fail-closed-admission-gate.yml`.
