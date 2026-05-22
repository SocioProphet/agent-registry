# Workspace Context Authority Binding

## Purpose

This document defines the Agent Registry binding for Prophet Workspace Context Fabric.

Prophet Workspace owns the Workroom and Context Fabric domain contracts. Agent Registry owns agent identity, sessions, authority state, grants, and revocation references consumed by those workspace contracts.

## Object

The first binding object is:

```text
contracts/workspace-context/workspace-context-authority-binding.v0.1.schema.json
contracts/workspace-context/workspace-context-authority-binding.v0.1.example.json
```

## Boundary

Agent Registry does not store workspace context graphs. It records the authority references needed for a workroom runtime binding to be admitted and audited.

The binding includes:

- workroom ref;
- context graph ref;
- runtime binding ref;
- agent refs;
- session refs;
- authority current-state refs;
- grant refs;
- revocation refs;
- evidence refs;
- policy refs.

## Validation

```bash
make validate-workspace-context-authority-binding
```
