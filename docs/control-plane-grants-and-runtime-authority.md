# Control-Plane Grants and Runtime Authority

This document records the Agent Registry side of the Matrix / MCP / A2A / capability-lease control-plane slice.

## Role

Agent Registry is the canonical registry for:

- agent specifications,
- agent identities,
- sessions,
- tool grants,
- grant revocation,
- and runtime authority records.

It does not own broker enforcement, deployment topology, Matrix room policy, or execution runtime.

## Boundary split

- `agent-registry` owns grant and authority records.
- `mcp-a2a-zero-trust` consumes grant and authority records for broker enforcement and zero-trust boundary checks.
- `HolographMe` owns human delegation, consent, and acting-for-human authority semantics.
- `agentplane` owns execution admission and run/replay evidence once work is proposed for execution.
- `policy-fabric` owns policy approvals and compiled policy evidence.

## Control-plane grant requirements

A control-plane grant record should include:

- stable grant identifier,
- subject agent,
- allowed capability or tool scope,
- authority class,
- optional human delegation reference,
- optional policy reference,
- optional admission reference,
- revocation status,
- and expiry or renewal posture.

## Non-goals

This tranche does not implement broker enforcement.

The broker/enforcement implementation belongs in `mcp-a2a-zero-trust` and should consume Agent Registry decisions rather than redefine them.
