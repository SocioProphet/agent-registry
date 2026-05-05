# OrgGov Actor Authority Bindings

## Purpose

OrgGov Actor Authority Bindings make Agent Registry the authority ledger for Organization Governance Control Plane v0.

The registry must answer:

```text
who or what acted → in which workroom → under which role → with which authority → under which policy → against which asset → with which evidence and revocation posture
```

## Product loop binding

The binding supports the shared OrgGov loop:

```text
Objective → Workroom → Actor → Role → Policy → Asset → Action → Evidence → Review → Outcome → Score → Learning
```

Agent Registry owns the `Actor`, `Role`, `RoleBinding`, `Authority`, `CapabilityGrant`, session, grant status, and revocation side of that loop.

## Contract files

- `contracts/orggov/actor-authority-binding.v0.1.schema.json`
- `contracts/orggov/actor-authority-binding.v0.1.example.json`
- `tools/validate_orggov_authority_bindings.py`

## Invariants

- Every role binding must point to an actor and a role.
- Every role must point to an authority.
- Every capability grant must have a status and expiration.
- Every active binding must be scoped to a workroom and work order.
- Policy references remain external to Policy Fabric.
- Evidence references remain external to AgentPlane, platform, workspace, and ledger systems.
- Revocation must be explicit and evidence-backed.

## Non-goals

- Agent Registry is not the policy engine.
- Agent Registry is not the execution plane.
- Agent Registry must not store credentials or private prompts.
- Agent Registry must not decide outcomes; it records authority posture and revocation posture.

## Estate links

- Parent tranche: `SocioProphet/prophet-platform#406`
- Registry workstream: `SocioProphet/agent-registry#18`
- Workspace control room: `SocioProphet/prophet-workspace#15`
- Policy gates: `SocioProphet/policy-fabric#57`
- Execution evidence: `SocioProphet/agentplane#104`
