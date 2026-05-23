# Control-Plane Grants and Runtime Authority

## Purpose

This document records the Agent Registry side of the Matrix / MCP / A2A / capability-lease control-plane slice.

## Role

Agent Registry is the canonical registry for:

- agent specifications;
- agent identities;
- sessions;
- tool grants;
- grant revocation;
- runtime authority records.

It does not own broker enforcement, deployment topology, Matrix room policy, or execution runtime.

## Boundary split

| Concern | Owner |
|---|---|
| Grant and runtime-authority records | `agent-registry` |
| Broker enforcement and zero-trust checks | `mcp-a2a-zero-trust` |
| Human delegation and consent authority | `HolographMe` |
| Execution admission and run/replay evidence | `agentplane` |
| Policy approvals and compiled policy evidence | `policy-fabric` |

## Contract

The first contract is:

```text
contracts/control-plane/control-plane-capability-grant.v0.1.schema.json
contracts/control-plane/control-plane-capability-grant.v0.1.example.json
```

A control-plane capability grant records:

- stable grant identifier;
- subject agent;
- authority class;
- allowed scopes;
- denied scopes;
- runtime authority status;
- expiry;
- policy reference;
- optional delegation reference;
- optional admission reference.

## Non-goals

This tranche does not implement broker enforcement.

Broker/enforcement implementation belongs in `mcp-a2a-zero-trust` and should consume Agent Registry decisions rather than redefine them.

## Validation

```bash
make validate-control-plane-capability-grant
```
