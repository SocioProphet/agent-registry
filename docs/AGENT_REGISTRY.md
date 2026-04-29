# Agent Registry

Agent Registry records governed agent identity, session authority, tool grants, revocation state, and evidence references for SocioProphet model fabric.

It is not an identity provider and does not grant live runtime authority in this first slice. It records deterministic, reference-only examples that Model Router, Guardrail Fabric, Model Governance Ledger, Prophet Platform, and Prophet CLI can consume.

## Role in model fabric

- `model-router` uses agent authority as a routing input.
- `guardrail-fabric` uses authority context as policy input.
- `model-governance-ledger` stores authority/session evidence refs.
- `prophet-cli` delegates `prophet agent registry list` here once packaging lands.

## First record kinds

- `AgentSpec`
- `ToolGrant`
- `SessionAuthority`
- `RevocationRecord`

## Authority boundary

This repository records authority claims and revocation records. It must not store secrets, credentials, tokens, raw private prompts, or live identity-provider state.

Tool grants are constrained by reference-only policy and evidence requirements.

## Validation

```bash
make validate
make test
```
