# Workspace Operations Registry

## Purpose

Extend Agent Registry so every agent action in the Workspace Operation Plane has registered identity, declared capabilities, scoped delegation, budgets, policy profile, audit level, and revocation state.

No agent receives workspace authority from presence alone. Authority must be registered, delegated, scoped, policy-checked, budgeted, and revocable.

## Hard rule

> AgentPlane must check this registry before any agent command touches: WorkspaceOperation, OperationTask, Artifact, DecisionCard, PolicyGateRecord, ToolGrant, Memory namespace, or Local agent-machine execution.

## Record kinds

| Kind | Description |
|---|---|
| `AgentRegistration` | Root identity record. Links agent to owner, policy profile, and revocation anchor. |
| `AgentCapabilityDeclaration` | Declares allowed operation types, tools, and artifact types. |
| `AgentOperationScope` | Constrains operation types and artifact types the agent may act upon in a given scope. |
| `AgentDelegationGrant` | Scoped, expiring, revocable delegation of operation authority from one agent to another. |
| `AgentToolGrant` | Grants specific tools with scope constraints and an expiration. Requires `evidence-required` constraint. |
| `AgentBudgetPolicy` | Token, operation, and artifact budgets plus `maxConcurrency`. |
| `AgentAuditProfile` | Audit level (`none` / `summary` / `standard` / `full`) and policy profile. |
| `AgentRevocationRecord` | Revocation state for the agent, including revoked operation types and tools. |
| `AgentOperationSessionBinding` | Binds an active session to its scope, delegation grant, tool grants, budget, and audit profile. |

## Required fields summary

| Field | Records |
|---|---|
| `agentId` | All |
| `ownerRef` | AgentRegistration |
| `version` | AgentRegistration metadata |
| `allowedOperationTypes` | AgentCapabilityDeclaration, AgentOperationScope, AgentDelegationGrant |
| `allowedTools` | AgentCapabilityDeclaration, AgentToolGrant |
| `allowedArtifactTypes` | AgentCapabilityDeclaration, AgentOperationScope, AgentDelegationGrant |
| `defaultBudget` | AgentBudgetPolicy |
| `maxConcurrency` | AgentBudgetPolicy |
| `policyProfile` | AgentRegistration, AgentCapabilityDeclaration, AgentOperationScope, AgentDelegationGrant, AgentBudgetPolicy, AgentAuditProfile |
| `auditLevel` | AgentAuditProfile |
| `revocationState` | AgentRegistration, AgentDelegationGrant, AgentRevocationRecord |
| `delegatedBy` | AgentDelegationGrant |
| `expiresAt` | AgentDelegationGrant, AgentToolGrant |

## Contract files

- `contracts/workspace-operations/records.v0.1.schema.json`
- `examples/workspace-operations/agent-registrations.example.json`
- `examples/workspace-operations/capability-declarations.example.json`
- `examples/workspace-operations/operation-scopes.example.json`
- `examples/workspace-operations/delegation-grants.example.json`
- `examples/workspace-operations/tool-grants.example.json`
- `examples/workspace-operations/budget-policies.example.json`
- `examples/workspace-operations/audit-profiles.example.json`
- `examples/workspace-operations/revocation-records.example.json`
- `examples/workspace-operations/session-bindings.example.json`

## Validation

```bash
make validate
make validate-workspace-ops
make test
```

## Invariants

- Every `AgentRegistration` must have a `revocationRef` that points to an existing `AgentRevocationRecord`.
- Every `AgentToolGrant` must include the `evidence-required` constraint.
- Every `AgentDelegationGrant` must have `delegatedBy`, `expiresAt`, and `revocationState`.
- Every `AgentOperationSessionBinding` must reference a registered agent, an existing `AgentOperationScope`, and at least one existing `AgentToolGrant`.
- `AgentBudgetPolicy.maxConcurrency` must be a positive integer.
- `AgentAuditProfile.auditLevel` must be one of: `none`, `summary`, `standard`, `full`.

## Non-goals

- Agent Registry is not the policy engine.
- Agent Registry is not the execution plane.
- Agent Registry must not store credentials, tokens, or private prompts.
- Agent Registry does not decide outcomes; it records authority posture and revocation posture.

## References

- `SocioProphet/agentplane#85`
- `SocioProphet/prophet-core-contracts#1`
- `SocioProphet/workspace-inventory#3`
- `SocioProphet/policy-fabric#46`
- `SourceOS-Linux/agent-machine#18`
