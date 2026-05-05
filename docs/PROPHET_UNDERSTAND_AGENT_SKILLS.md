# Prophet Understand Agent Skills

## Purpose

Agent Registry is the source of truth for portable Prophet Understand / Repo Intelligence agent skills.

The goal is one canonical skill definition that can be rendered into agent-facing surfaces without creating per-agent schema forks.

## Canonical skill

Skill ID:

```text
prophet-understand.v0
```

Primary artifact:

```text
.prophet/prophet-understanding.json
```

Normative platform contract:

```text
SocioProphet/prophet-platform/schemas/repo-intelligence/prophet-understanding.schema.json
```

## Skill actions

- `repo.scan`: run or request a bounded repo graph scan.
- `repo.validate_graph`: validate a graph artifact and report missing/stale/invalid facts.
- `repo.guided_tour`: produce a guided tour from graph nodes and edges.
- `repo.diff_impact`: map changed paths to affected nodes, edges, tests, docs, and policies.
- `repo.graph_aware_review`: review PRs using affected graph facts.
- `repo.graph_aware_fix_plan`: propose bounded repair steps without granting mutation authority.

## Required agent behavior

Every generated answer must:

- cite node IDs, edge IDs, source anchors, or validation records when available
- preserve provenance receipt IDs
- preserve policy and validation status
- mark inferred graph facts as inferred
- avoid invented ownership, dependency, or test-coverage claims
- avoid reading or exfiltrating secret-like paths
- avoid enabling post-commit hooks or local file-serving surfaces without explicit review
- emit validation evidence before claiming completion

## Supported surfaces

Initial render targets:

- Copilot instructions
- Codex task prompts
- OpenClaw skill manifest
- Claude-style tool instructions
- Cursor/OpenCode-style repository rules
- Gemini-style CLI instructions
- VS Code workspace task documentation

## Non-goals

- No agent-specific schema fork.
- No mutation authority from graph output alone.
- No direct dependency on a third-party plugin system as a trust root.
