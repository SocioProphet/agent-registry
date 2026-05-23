# Workspace Context Authority Binding

## Purpose

This document defines the Agent Registry authority-side binding for Prophet Workspace Context Fabric.

Prophet Workspace owns Workroom and Context Fabric semantics. Agent Registry owns the agent, session, authority-state, grant, revocation, policy, and evidence references consumed by workspace runtime bindings.

## Object

The first binding object is:

```text
contracts/workspace-context/workspace-context-authority-binding.v0.1.schema.json
contracts/workspace-context/workspace-context-authority-binding.v0.1.example.json
```

## Boundary

Agent Registry does not store workspace context graphs and does not own context-pack memory.

Agent Registry records the authority references needed for a workroom runtime binding to be admitted and audited.

The binding includes:

- workroom ref;
- optional professional workroom ref;
- context graph ref;
- runtime binding ref;
- agent refs;
- session refs;
- authority current-state refs;
- grant refs;
- revocation refs;
- evidence refs;
- policy refs.

## Plane ownership

| Concern | Owner |
|---|---|
| Workroom and Context Fabric semantics | Prophet Workspace |
| Authority refs, grants, revocations, sessions | Agent Registry |
| Execution evidence | AgentPlane |
| Recall and context packs | Memory Mesh |
| Runtime and product evidence records | Prophet Platform |

## Validation

```bash
make validate-workspace-context-authority-binding
```

## Non-goals

This binding does not:

- store workspace context graphs;
- store raw context packs;
- grant runtime authority by itself;
- execute work;
- replace AgentPlane execution evidence;
- replace Memory Mesh recall authority.
