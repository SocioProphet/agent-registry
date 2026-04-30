# SourceOS / NLBoot Program Status

This ledger tracks the current work lanes for SourceOS, NLBoot, developer tools, packaging, and dashboard integration.

Percentages are pragmatic execution-readiness estimates, not claims of production completeness. A lane reaches 100% only when code/docs/tests/CI/release or PR merge criteria are complete for the current milestone.

## Current milestone

Milestone: M2 usable proof and M3 integration scaffolding.

Goal: prove a local-first SourceOS/NLBoot lifecycle path on the M2 demo surface while keeping generic Linux/Purism/VM paths alive and preparing installable developer/operator tooling.

## Lane status

| Lane | Current % | Current state | Next action |
| --- | ---: | --- | --- |
| NLBoot usable MVP | 88% | Rust planner, signature verification, artifact fetch/cache/evidence, Linux dry-run proof, final handoff gate, M2 adapter dry-run, Cargo.lock committed, release-candidate workflow proven twice, SBOM helper added, SBOM-enabled RC workflow proven, RC artifact uploaded with SBOM path, operator-test release notes drafted. | Cut first operator-test tag only after final release-note review and downstream release decision. |
| SourceOS devtools | 74% | `sourceosctl` read-only/dry-run scaffold merged; schema-backed NLBoot evidence validation PR #5 merged and issue #3 closed; superseded draft PR #4 closed. | Add package/install surface and release artifact inspection integration. |
| SourceOS spec schemas | 70% | NLBoot schemas plus ReleaseSet/Fingerprint/ConfigSource/TokenDoor/GitRefBuild schemas merged; issues #68 and #72 closed. | Use schemas downstream in devtools/web/boot; add negative examples and conformance matrices later. |
| SourceOS boot integration | 74% | NLBoot integration and M2 packaging specs merged; AppleSiliconAdapterEvidence normalization PR #17 merged and issue #15 closed; superseded draft PR #16 closed. | Move to Recovery/Installer artifact build lane and platform-entry descriptor adapter task. |
| SocioProphet Web evidence UI | 60% | NLBoot evidence dashboard PR #21 merged and issue #20 closed after product-build passed. | Add schema-backed fixtures/API integration later; current mock dashboard slice complete. |
| Homebrew packaging | 55% | NLBoot release-template workflow PR #8 merged; issue #6 closed. No active formula with fake hashes. | Publish real NLBoot release, then run generation workflow for versioned formula. |
| Agent dispatch operations | 93% | Dossier added, repo instructions in place, Copilot assignment working, PR creation/review/merge loop active, duplicate draft PRs cleaned up, SBOM proof PR #9 merged. | Continue PR sweep, merge clean PRs, update ledger each turn. |
| M2 platform proof | 66% | M2 adapter dry-run evidence path exists; sourceos-spec has Apple Silicon adapter evidence schema; M2 normal and Recovery/Installer packaging spec and normalization design/fixtures merged. | Move to Recovery/Installer artifact build lane and platform-entry descriptor implementation planning. |

## Active issue and PR queue

| Repo | Issue | PR | State | Owner signal | Next action |
| --- | ---: | ---: | --- | --- | --- |
| `SourceOS-Linux/sourceos-devtools` | #1 | #2 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-devtools` | #3 | #5 | merged / closed | Copilot + ChatGPT replacement PR | complete for current slice. |
| `SourceOS-Linux/sourceos-boot` | #11 | #12 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-boot` | #13 | #14 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-boot` | #15 | #17 | merged / closed | Copilot + ChatGPT replacement PR | complete for current slice. |
| `SourceOS-Linux/sourceos-spec` | #68 | #69 | merged / closed | Copilot | complete for current slice. |
| `SourceOS-Linux/sourceos-spec` | #72 | #73 | merged / closed | Copilot | complete for current slice. |
| `mdheller/socioprophet-web` | #20 | #21 | merged / closed | Copilot | complete for current slice. |
| `SocioProphet/homebrew-prophet` | #6 | #8 | merged / closed | Copilot | complete for current slice. |
| `SociOS-Linux/nlboot` | repo-local | #8 | merged | ChatGPT | release-candidate proof complete. |
| `SociOS-Linux/nlboot` | repo-local | #9 | merged | ChatGPT | SBOM-enabled release-candidate proof complete. |

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
- `SourceOS-Linux/sourceos-spec#73` merged and `#72` closed.
- `SociOS-Linux/nlboot#8` merged after validation and release-candidate workflows passed; RC artifact `nlboot-client-release-candidate` uploaded with digest `sha256:fece6f08819baa8f0f1152e42c1e7121378dc490c941d99604e6cee7854bff10`.
- `SociOS-Linux/nlboot` now has deterministic `tools/cargo_metadata_to_spdx.py` SBOM helper.
- `SociOS-Linux/nlboot` release-candidate and tagged release workflows are wired to include `sbom.spdx.json`.
- `SociOS-Linux/nlboot` has draft `docs/RELEASE_NOTES_NLBOOT_CLIENT_V0_1_0_OPERATOR_TEST.md`.
- `SociOS-Linux/nlboot#9` merged after validation and SBOM-enabled release-candidate workflows passed; RC artifact `nlboot-client-release-candidate` uploaded with digest `sha256:a711b0abbcab5c72105bf80728e82963859883bd205ee7ce923ea690ce9433cb`.
- `SourceOS-Linux/sourceos-devtools#5` merged and `#3` closed; superseded draft `#4` closed.
- `SourceOS-Linux/sourceos-boot#17` merged and `#15` closed; superseded draft `#16` closed.

## Percentage policy

- 0–20%: repo/task created, no meaningful artifact yet.
- 20–40%: scaffolding, docs, instructions, issue dispatch, or initial fixtures exist.
- 40–60%: implementation slice exists but not fully integrated or released.
- 60–80%: working proof with tests/CI/docs, but not fully packaged or integrated across dependent repos.
- 80–95%: release/integration ready, pending final checks, merge, or production-equivalent proof.
- 100%: milestone complete, merged, validated, and ledger updated.
