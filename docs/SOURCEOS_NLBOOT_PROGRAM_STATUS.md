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
| SourceOS devtools | 62% | `sourceosctl` read-only/dry-run scaffold PR #2 merged; issue #1 closed. | Add package/install surface, schema-backed evidence validation, and NLBoot release inspection integration. |
| SourceOS spec schemas | 58% | NLBoot object schemas PR #69 merged; issue #68 closed. Canonical contracts now exist for current slice. | Add ReleaseSet, Fingerprint, ConfigSource, TokenDoor, and GitRefBuild schemas. |
| SourceOS boot integration | 66% | NLBoot integration PR #12 merged; M2 Recovery/Installer packaging PR #14 merged and issue #13 closed. | Add AppleSiliconAdapterEvidence normalization and platform-entry descriptor adapter task. |
| SocioProphet Web evidence UI | 60% | NLBoot evidence dashboard PR #21 merged and issue #20 closed after product-build passed. | Add schema-backed fixtures/API integration later; current mock dashboard slice complete. |
| Homebrew packaging | 55% | NLBoot release-template workflow PR #8 merged; issue #6 closed. No active formula with fake hashes. | Publish real NLBoot release, then run generation workflow for versioned formula. |
| Agent dispatch operations | 87% | Dossier added, repo instructions in place, Copilot assignment working, PR creation/review/merge loop active, M2 packaging PR merged after validation evidence. | Continue PR sweep, merge clean PRs, update ledger each turn. |
| M2 platform proof | 54% | M2 adapter dry-run evidence path exists; sourceos-spec has Apple Silicon adapter evidence schema; M2 normal and Recovery/Installer packaging spec and dry-run fixtures merged. | Move to Recovery/Installer artifact build lane and Apple Silicon adapter evidence normalization. |

## Active issue and PR queue

| Repo | Issue | PR | State | Owner signal | Next action |
| --- | ---: | ---: | --- | --- | --- |
| `SourceOS-Linux/sourceos-devtools` | #1 | #2 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-boot` | #11 | #12 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-boot` | #13 | #14 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-spec` | #68 | #69 | merged / closed | Copilot | complete for current slice. |
| `mdheller/socioprophet-web` | #20 | #21 | merged / closed | Copilot | complete for current slice. |
| `SocioProphet/homebrew-prophet` | #6 | #8 | merged / closed | Copilot | complete for current slice. |

## Completed administrative items

- `SourceOS-Linux/sourceos-devtools` created and bootstrapped.
- `SourceOS-Linux/sourceos-spec#70` closed as completed.
- Standard `AGENTS.md` and `.github/copilot-instructions.md` added to active repos.
- NLBoot dry-run operator quickstart added.
- Agent dispatch and merge operations dossier added to `SocioProphet/agent-registry`.
- `SourceOS-Linux/sourceos-boot#12` merged and `#11` closed.
- `SourceOS-Linux/sourceos-spec#69` merged and `#68` closed.
- `SourceOS-Linux/sourceos-devtools#2` merged and `#1` closed.
- `SocioProphet/homebrew-prophet#8` merged and `#6` closed.
- `mdheller/socioprophet-web#21` merged and `#20` closed.
- `SourceOS-Linux/sourceos-boot#14` merged and `#13` closed.

## Percentage policy

- 0–20%: repo/task created, no meaningful artifact yet.
- 20–40%: scaffolding, docs, instructions, issue dispatch, or initial fixtures exist.
- 40–60%: implementation slice exists but not fully integrated or released.
- 60–80%: working proof with tests/CI/docs, but not fully packaged or integrated across dependent repos.
- 80–95%: release/integration ready, pending final checks, merge, or production-equivalent proof.
- 100%: milestone complete, merged, validated, and ledger updated.
