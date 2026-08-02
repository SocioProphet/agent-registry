# agent-registry

Governed registry for SocioProphet agent specs, identities, sessions, memories, tool grants, revocation, and runtime authority.

## Role

Agent Registry owns the agent identity, capability, allowed-surface, authority, and revocation boundary for SocioProphet agents.

It records what an agent is allowed to do, which tools/models/datasets/memory scopes/runtimes it may touch, and whether the agent is active, reduced, suspended, or revoked. It does not grant live credentials by itself and does not replace runtime, model, policy, guardrail, or execution evidence authorities.

## Prophet Trust Chain agent manifest bindings

Agent Registry owns the agent-manifest slice of Prophet Trust Chain. The platform standard and admission contract live in `SocioProphet/prophet-platform`:

- `docs/standards/PROPHET_TRUST_CHAIN_V0.md`
- `docs/TRUST_CHAIN_ADMISSION_CONTRACT.md`
- `docs/standards/PROPHET_TRUST_CHAIN_IMPLEMENTATION_MAP.md`

This repo now carries `TrustChainAgentManifestBinding`, which binds an agent identity and capability profile to allowed tools, model routes, datasets, memory scopes, runtime classes, policy/admission refs, Guardrail decision refs, AgentPlane validation refs, and downgrade/revocation posture.

Relevant files:

- `schemas/trust-chain-agent-manifest-binding.v0.1.schema.json`
- `examples/trust-chain-agent-manifest-binding.preview.example.json`
- `examples/trust-chain-agent-manifest-binding.blocked.json`
- `tools/validate_trust_chain_agent_manifest_binding.py`
- `tools/tests/test_trust_chain_agent_manifest_binding.py`

Validation:

```bash
make validate-trust-chain-agent-manifest-binding
python3 -m pytest -q tools/tests/test_trust_chain_agent_manifest_binding.py
```

The preview fixture allows the agent only with review-required autonomy and proposal-only effect posture. It requires runtime, model, tool, policy, guardrail, and AgentPlane validation refs before the preview binding is accepted.

The blocked production fixture proves fail-closed behavior: production agent execution is denied, authority is reduced, and remediation is required when runtime/model/tool/AgentPlane evidence is missing.

Boundary: Agent Registry records identity, capability, allowed-surface, authority, and downgrade/revocation posture. It does not grant live credentials, certify runtime production readiness, replace Lattice Forge runtime evidence, replace Model Governance Ledger model promotion evidence, replace Policy Fabric policy profiles, replace Guardrail Fabric action admission, replace AgentPlane validation/replay/receipt evidence, or replace Prophet Platform admission composition.

## Validation

General validation:

```bash
make validate
make test
```

Trust Chain-specific validation:

```bash
make validate-trust-chain-agent-manifest-binding
```

## Fail-closed admission gate (INV-ACC-1 — no invisible authority)

Standard 030 invariant **INV-ACC-1**: an agent that declares capabilities MUST
resolve to a registry admission entry. Capability without admission = denied.
`tools/fail_closed_admission_gate.py` enforces it, gating a declared-capability
record against `agents/admissions/*.admission.json`
(`schemas/agent-admission-manifest.v0.1.schema.json`): a granted admission passes
(exit 0); a `proposed` stub is review-required (exit 3, never auto-authorized);
capability with no admission entry is denied (exit 1). See
`docs/fail-closed-admission-gate.md` and `agents/admissions/README.md`.

```bash
make validate-fail-closed-admission-gate
python3 -m pytest -q tools/tests/test_fail_closed_admission_gate.py
```

## Invariants

- No invisible authority: a capability-bearing agent with no resolvable admission entry is denied (INV-ACC-1).
- No broad tool rights by default.
- No production agent execution without runtime, model, tool, policy, guardrail, and AgentPlane evidence.
- No production authority when the agent is reduced, suspended, or revoked.
- No live credential handling in the registry contract layer.
- Agent outputs remain subject to Guardrail Fabric and Sociosphere admission flow.
