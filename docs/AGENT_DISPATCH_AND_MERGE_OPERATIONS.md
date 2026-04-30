# Agent Dispatch and Merge Operations Dossier

This is the operating manual for farming work across GitHub using Copilot, Codex, and ChatGPT as the coordinating, review, and merge layer.

## Core correction

Assignment to `copilot-swe-agent[bot]` is the reliable Copilot trigger.

`@copilot` comments are useful backup signals, but assignment is what causes real Copilot PRs to appear.

`@codex` comments can engage Codex, but Codex comments do not count as delivery unless a GitHub branch, PR, commit, or merge exists.

## Operating principle

Issue = work order.

Copilot assignment = reliable executor trigger.

Codex comment = parallel or backup signal.

PR = delivery artifact.

Workflow output = validation evidence.

Merge = completion.

Do not count agent response as work complete.

Codex comments count as engaged, not delivered, unless a GitHub PR, branch, commit, or merge is verified.

Copilot PRs count as delivered candidates, not complete, until reviewed, checked, merged, and parent issue closed.

## Roles

### Human owner

The human owner should not be the routine execution bottleneck.

Human owner involvement is reserved for:

- high-risk merge decisions;
- repo/admin settings;
- credential and secret decisions;
- production deployment authorization;
- policy or architecture escalation.

### Coordinating assistant

The coordinating assistant acts as queue manager, dispatcher, reviewer, and merge operator.

Responsibilities:

- create bounded issues;
- assign Copilot correctly;
- comment to Codex and Copilot;
- verify PRs exist;
- inspect scope;
- inspect checks;
- request fixes;
- approve and merge clean PRs;
- close parent issues;
- update ledgers and status docs;
- remove the human owner from routine bottlenecks where appropriate.

### Copilot

Copilot is best for bounded implementation PRs.

Use for:

- tests;
- docs;
- fixtures;
- validators;
- small APIs;
- workflow wiring;
- repo-local implementation tasks.

Reliable trigger:

- assign issue to `copilot-swe-agent[bot]`.

### Codex

Codex is useful as a parallel backup, analysis agent, or implementation attempt when Copilot is unavailable.

Trigger:

```md
@codex Please take this in the <repo> Codex environment...
```

Delivery must still be verified through GitHub-side evidence: PR, branch, commit, merge, or visible artifact.

## Repo settings baseline

For low-risk repos:

- disable workflow-run approval requirement for Copilot cloud-agent tasks where appropriate;
- keep status checks before merge enabled;
- manual review may be off or path-scoped;
- auto-merge may be enabled if visible and safe;
- delete head branches after merge;
- signed commits are optional for Copilot-heavy repos;
- do not expose secrets to PR workflows;
- avoid `pull_request_target` unless explicitly reviewed.

High-risk paths still require manual review:

- privileged workflow changes;
- secrets or tokens;
- release automation;
- deployment;
- boot, install, or recovery;
- host mutation;
- SourceOS low-level mutation;
- runtime admission;
- Lattice admission;
- production infrastructure;
- defense or public-safety effects-linked execution.

## Required repo instruction files

Every active repo should eventually include:

```text
.github/copilot-instructions.md
AGENTS.md
```

### Standard `AGENTS.md`

```md
# Agent Operating Instructions

Work issue-first.

Rules:
- One repo, one issue, one PR.
- Inspect the live repository before editing.
- Keep scope bounded to the issue body.
- Do not broaden scope without asking in the issue.
- Do not touch unrelated files.
- Do not claim production readiness unless acceptance criteria prove it.
- Include validation evidence in the PR body.
- Leave known gaps explicit.

PR body must include:
- What changed.
- Exact commands run.
- Pass/fail output summary.
- Known gaps.
- Anything blocked.

Never:
- Commit secrets, tokens, credentials, or private keys.
- Invent release URLs, checksums, SBOMs, or provenance.
- Admit runtimes to production from fixture proofs.
- Claim live ingestion when only fixture validation exists.
- Claim safety-critical authority from advisory data.
```

### Standard `.github/copilot-instructions.md`

```md
Use the GitHub issue body as the source of truth.

Before editing:
1. Read the issue.
2. Inspect the repo.
3. Identify existing validation commands.
4. Keep the PR bounded.

When implementing:
- Prefer existing repo patterns.
- Add tests, fixtures, or validators with the implementation.
- Keep generated files only if repo conventions require them.
- Do not modify unrelated workflows or policy files.

When opening the PR:
- Link the issue.
- Include validation evidence.
- List known gaps.
- State non-goals preserved.
- Do not mark ready if validation did not run.
```

## Issue template

```md
## Target repo
`OWNER/REPO`

## Context
Brief explanation of why this task exists and what upstream work it relates to.

## Scope
Implement the smallest bounded change that does the following:
1. ...
2. ...
3. ...

## Acceptance criteria
- ...
- ...
- PR body includes validation evidence.

## Validation commands
Expected commands:
```bash
<command>
<command>
```

If repo-native commands differ, inspect and use repo-native commands.

## Boundaries / non-goals
- Do not ...
- Do not ...
- Do not touch other repositories.
- Do not claim production readiness unless explicitly requested and proven.

## PR requirements
Open one PR against the default branch. Include:
- what changed;
- exact commands run;
- pass/fail output summary;
- known gaps;
- anything blocked.
```

## Dispatch comments

After the issue exists, add compact routing comments.

### Codex

```md
@codex Please take this in the <OWNER/REPO> Codex environment. One PR: <task summary>. Inspect the repo first and include validation evidence.
```

### Copilot

```md
@copilot Please take this if available. Keep it bounded to <scope>. Open one PR with validation evidence.
```

### Copilot assignment

Assign the issue to:

```text
copilot-swe-agent[bot]
```

In GitHub UI this appears as Copilot.

## Queue states

| State | Meaning |
| --- | --- |
| created | Issue exists. |
| dispatched | Codex/Copilot comments posted. |
| assigned | Copilot assigned. |
| engaged | Agent commented or branch appeared. |
| pr_open | Real GitHub PR exists. |
| checks_pending | Checks queued, running, or action-required. |
| needs_fix | PR exists but scope or checks are wrong. |
| draft | PR exists but cannot merge yet. |
| ready_review | Scope looks right and checks are green. |
| auto_merge_enabled | Waiting for required queued checks only. |
| merged | PR merged. |
| closed | Parent issue closed. |
| blocked | External, admin, or manual blocker. |

## Review and merge loop

For each open issue:

1. Check if there is an active PR.
2. If no PR:
   - ensure Copilot is assigned;
   - ensure Codex/Copilot comments exist;
   - wait or dispatch again.
3. If PR exists:
   - inspect changed files;
   - compare to issue scope;
   - check workflow runs;
   - comment/request changes if incomplete;
   - approve and merge if clean.
4. Close parent issue after merge.
5. Update program ledger if the work changes program state.

## Scope review checklist

Ask:

- Does the PR satisfy issue acceptance criteria?
- Does it preserve non-goals?
- Did it touch only expected files?
- Did it include validation evidence?
- Are generated files expected?
- Are docs, tests, or validators included where needed?

## Merge checklist

Merge only when:

- PR is not draft;
- changed files match scope;
- checks are green;
- validation evidence is in the PR body;
- no high-risk files were touched unexpectedly;
- no unresolved review threads remain;
- no non-goal violation exists;
- expected head SHA matches before merge.

Use squash merge by default.

If only a long-running queued check remains and auto-merge is safe, enable auto-merge.

## Standard PR comments

### Scoped and waiting on checks

```md
Agent triage: scope matches the issue. Waiting on workflow runs before merge.
```

### Stuck at action_required

```md
@copilot Scope looks correct, but workflows are stuck at `action_required`. Please refresh/rebase or push a no-op commit if needed so checks rerun under current repo settings. Do not broaden scope.
```

### Draft but clean

```md
@copilot Scope and validation look good. Please mark this PR ready for review so it can be approved and merged. Keep scope unchanged.
```

### Stale issue refs

```md
@copilot This PR appears to use stale issue refs. Please update against the current open queue before marking ready. Keep scope bounded and rerun validation.
```

### Codex claims PR but no PR exists

```md
@codex Follow-up verification: your task response claims a commit/PR, but I cannot verify a GitHub PR, branch, or commit in this repo.

Please either open the GitHub PR against this issue, or report what blocked PR/branch creation. Keep the same bounded scope and include validation evidence.
```

## Risk rules

Low-risk repos can run this automated loop aggressively:

- prophet-platform;
- socioprophet;
- gaia-world-model;
- sociosphere;
- sherlock-search;
- meshrush;
- agent-registry;
- homebrew-prophet;
- standards repos.

High-risk work still requires explicit gates:

- SourceOS boot, install, or recovery;
- host mutation;
- secrets and tokens;
- release publishing;
- production deployment;
- Lattice admission;
- Agentplane production execution;
- defense or public-safety effects-linked workflows.

For high-risk work:

1. docs/spec first;
2. fixtures second;
3. tests third;
4. dry-run fourth;
5. real mutation only behind explicit review.

## Short version for other agents

```md
Work issue-first.
1. Create a bounded GitHub issue.
2. Put full scope, acceptance criteria, validation commands, and non-goals in the issue body.
3. Dispatch:
   @codex Please take this in the <repo> Codex environment. One PR: <task>. Inspect the repo first and include validation evidence.
   @copilot Please take this if available. Keep it bounded to <scope>. Open one PR with validation evidence.
4. Assign Copilot with `copilot-swe-agent[bot]`.
5. Do not count agent comments as completion.
6. Count only GitHub PR, branch, commit, or merge as delivery.
7. Review PR scope and checks.
8. Request fixes if incomplete.
9. Approve and merge clean PRs.
10. Close parent issues.
11. Update the program ledger if program state changes.
```

This is the working SocioProphet agent-dispatch pattern.
