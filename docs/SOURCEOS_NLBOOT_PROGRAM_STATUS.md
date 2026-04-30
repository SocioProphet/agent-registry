# SourceOS / NLBoot Program Status

This ledger tracks the current work lanes for SourceOS, NLBoot, developer tools, packaging, and dashboard integration.

Percentages are pragmatic execution-readiness estimates, not claims of production completeness. A lane reaches 100% only when code/docs/tests/CI/release or PR merge criteria are complete for the current milestone.

## Current milestone

Milestone: M2 usable proof and M3 integration scaffolding.

Goal: prove a local-first SourceOS/NLBoot lifecycle path on the M2 demo surface while keeping generic Linux/Purism/VM paths alive and preparing installable developer/operator tooling.

## Lane status

| Lane | Current % | Current state | Next action |
| --- | ---: | --- | --- |
| NLBoot usable MVP | 72% | Rust planner, signature verification, artifact fetch/cache/evidence, Linux dry-run proof, final handoff gate, M2 adapter dry-run, release workflow, operator docs. | Commit Cargo.lock, add SBOM release artifact, prove release workflow. |
| SourceOS devtools | 32% | Repo created, README/scope/docs/agent instructions/maturity/Makefile/CI added; `sourceosctl` scaffold issue assigned. | Wait for Copilot PR or scaffold read-only CLI directly if idle. |
| SourceOS spec schemas | 25% | NLBoot schema issue assigned; repo instructions added. | Wait for Copilot PR; define BootPlan/ArtifactCache/Proof/Adapter schemas if idle. |
| SourceOS boot integration | 25% | NLBoot integration issue assigned; repo instructions added. | Wait for Copilot PR; add integration fixtures if idle. |
| SocioProphet Web evidence UI | 20% | Vue-shell issue assigned; repo instructions added. | Wait for Copilot PR; add mock NLBoot evidence dashboard if idle. |
| Homebrew packaging | 28% | Formula task assigned; NLBoot formula template exists in nlboot repo. | Wait for Copilot PR; align formula with release artifact names after release. |
| Agent dispatch operations | 65% | Dossier added to agent-registry; active issues assigned to Copilot; Codex/Copilot comments posted. | Continue PR sweep, review/merge loop, and close completed issues. |
| M2 platform proof | 38% | M2 adapter dry-run evidence path exists; actual Apple Silicon packaging/entry handling still pending. | Add SourceOS Recovery/Installer packaging spec and Asahi-compatible task packet. |

## Active issue queue

| Repo | Issue | State | Owner signal | Next action |
| --- | ---: | --- | --- | --- |
| `SourceOS-Linux/sourceos-devtools` | #1 | assigned | Copilot + Codex comments | Wait for PR; reinforce if idle. |
| `SourceOS-Linux/sourceos-boot` | #11 | assigned | Copilot + Codex comments | Wait for PR; reinforce if idle. |
| `SourceOS-Linux/sourceos-spec` | #68 | assigned | Copilot + Codex comments | Wait for PR; reinforce if idle. |
| `mdheller/socioprophet-web` | #20 | assigned | Copilot + Codex comments | Wait for PR; reinforce if idle. |
| `SocioProphet/homebrew-prophet` | #6 | assigned | Copilot + Codex comments | Wait for PR; reinforce if idle. |

## Completed administrative items

- `SourceOS-Linux/sourceos-devtools` created and bootstrapped.
- `SourceOS-Linux/sourceos-spec#70` closed as completed.
- Standard `AGENTS.md` and `.github/copilot-instructions.md` added to active repos.
- NLBoot dry-run operator quickstart added.
- Agent dispatch and merge operations dossier added to `SocioProphet/agent-registry`.

## Percentage policy

- 0–20%: repo/task created, no meaningful artifact yet.
- 20–40%: scaffolding, docs, instructions, issue dispatch, or initial fixtures exist.
- 40–60%: implementation slice exists but not fully integrated or released.
- 60–80%: working proof with tests/CI/docs, but not fully packaged or integrated across dependent repos.
- 80–95%: release/integration ready, pending final checks, merge, or production-equivalent proof.
- 100%: milestone complete, merged, validated, and ledger updated.
