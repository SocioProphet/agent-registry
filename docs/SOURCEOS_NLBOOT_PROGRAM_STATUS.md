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
| SourceOS devtools | 46% | Repo bootstrapped; `sourceosctl` scaffold PR #2 exists, scoped, but draft with workflow `action_required`. | Wait for Copilot to mark ready and rerun checks; review/merge when green. |
| SourceOS spec schemas | 58% | NLBoot object schemas PR #69 merged; issue #68 closed. Canonical contracts now exist for current slice. | Use schemas downstream in boot/devtools/web; add ReleaseSet/Fingerprint/TokenDoor next. |
| SourceOS boot integration | 56% | NLBoot integration docs/fixtures/validation/maturity PR #12 merged; issue #11 closed. | Add platform adapter specs and align to sourceos-spec schemas. |
| SocioProphet Web evidence UI | 34% | NLBoot evidence dashboard PR #21 exists but needs lockfile churn fixed before merge. | Wait for Copilot fix; re-review after lockfiles are reverted. |
| Homebrew packaging | 34% | NLBoot formula/update PR #8 exists but needs rebase and template-vs-active-formula correction. | Wait for Copilot fix; active formula must not contain placeholder SHA values. |
| Agent dispatch operations | 78% | Dossier added, instructions in active repos, Copilot assignment working, PR review/merge loop active. | Continue PR sweep, merge clean PRs, request fixes on unsafe scope. |
| M2 platform proof | 40% | M2 adapter dry-run evidence path exists; sourceos-spec now has Apple Silicon adapter evidence schema. | Add SourceOS Recovery/Installer packaging spec and Asahi-compatible implementation task. |

## Active issue and PR queue

| Repo | Issue | PR | State | Owner signal | Next action |
| --- | ---: | ---: | --- | --- | --- |
| `SourceOS-Linux/sourceos-devtools` | #1 | #2 | draft / action_required | Copilot | mark ready, refresh checks, then review/merge. |
| `SourceOS-Linux/sourceos-boot` | #11 | #12 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-spec` | #68 | #69 | merged / closed | Copilot | complete for current slice. |
| `mdheller/socioprophet-web` | #20 | #21 | needs_fix | Copilot | revert unrelated lockfile churn and rerun validation. |
| `SocioProphet/homebrew-prophet` | #6 | #8 | needs_fix / not mergeable | Copilot | rebase and move placeholder formula to template or wait for real release hashes. |

## Completed administrative items

- `SourceOS-Linux/sourceos-devtools` created and bootstrapped.
- `SourceOS-Linux/sourceos-spec#70` closed as completed.
- Standard `AGENTS.md` and `.github/copilot-instructions.md` added to active repos.
- NLBoot dry-run operator quickstart added.
- Agent dispatch and merge operations dossier added to `SocioProphet/agent-registry`.
- `SourceOS-Linux/sourceos-boot#12` merged and `#11` closed.
- `SourceOS-Linux/sourceos-spec#69` merged and `#68` closed.

## Percentage policy

- 0–20%: repo/task created, no meaningful artifact yet.
- 20–40%: scaffolding, docs, instructions, issue dispatch, or initial fixtures exist.
- 40–60%: implementation slice exists but not fully integrated or released.
- 60–80%: working proof with tests/CI/docs, but not fully packaged or integrated across dependent repos.
- 80–95%: release/integration ready, pending final checks, merge, or production-equivalent proof.
- 100%: milestone complete, merged, validated, and ledger updated.
