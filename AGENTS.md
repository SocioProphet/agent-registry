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
- Claim runtime authority beyond documented registry contracts.
- Admit agents, memories, tool grants, or sessions to production from fixture proofs.

Agent-registry-specific rules:
- This repo owns governed agent specs, identities, sessions, memories, tool grants, revocation records, and runtime authority contracts.
- Keep registry contracts separate from execution-plane behavior.
- Do not implement broad runtime execution here unless explicitly scoped.
- Document authority, revocation, and evidence boundaries clearly.

Validation:
- Use repository-native validation commands if present.
- Add Makefile or schema validation if adding examples.
