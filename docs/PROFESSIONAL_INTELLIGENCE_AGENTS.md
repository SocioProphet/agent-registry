# Professional Intelligence Agents

## Purpose

This document defines the first Agent Registry authority surface for the Professional Intelligence OS Gate 3 demo path.

Agent Registry does not execute agents. It records governed agent identity, scoped tool grants, session authority, revocation state, and evidence references that Agentplane, Policy Fabric, Model Router, Guardrail Fabric, Memory Mesh, Prophet Workspace, and Prophet Platform can consume.

## Registered agents

The seed Professional Intelligence agent set is defined in:

- `examples/professional-intelligence/agent-specs.example.json`

Initial agents:

- `opportunity-review-agent`
- `relationship-agent`
- `policy-review-agent`
- `workspace-setup-agent`

## Tool grants

Tool grants are defined in:

- `examples/professional-intelligence/tool-grants.example.json`

The grants are intentionally scoped and evidence-bound:

- read/evaluate search context;
- draft-only workroom update;
- read-only context access;
- evaluate-only policy checks;
- draft-only workroom creation.

No grant stores secrets, tokens, raw prompts, or live identity-provider state.

## Session and revocation

Session authority and revocation records are defined in:

- `examples/professional-intelligence/session-authority.example.json`
- `examples/professional-intelligence/revocation-record.example.json`

A session must reference registered agents and active grants. A revocation record must identify the agent and current revocation state.

## Validation

Professional Intelligence examples are included in the existing repo validation path:

```bash
make validate
make test
```

The validator also checks cross references:

- every agent grant reference exists;
- every grant references a registered agent;
- session authority references registered agents and grants;
- revocation records reference registered agents;
- every tool grant includes `evidence-required`.

## Gate 3 role

This work supports Gate 3 of the Professional Intelligence OS control register: create a runnable demo slice.

It supplies the authority and tool-grant layer for the Agentplane workflow bundle, the Prophet Workspace workroom fixture, Policy Fabric policy decisions, ContractForge obligations, and future Memory Mesh context packs.
