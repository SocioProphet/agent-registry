# Agent Admission Manifests (`agents/admissions/`)

Registry admission entries that realize **INV-ACC-1 — no invisible authority**
(`SocioProphet/socioprophet-agent-standards` Standard 030), closing
`SocioProphet/agent-registry#53`.

Each `*.admission.json` validates against
`schemas/agent-admission-manifest.v0.1.schema.json` and makes one
capability-bearing agent's authority **visible** to the registry. The
`tools/fail_closed_admission_gate.py` gate denies any agent that declares
capabilities but resolves to no admission entry here.

## Statuses (fail-closed)

| `admission_status` | `authority.granted` | Gate verdict | Meaning |
|---|---|---|---|
| `admitted` | `true` (+ non-empty `authority_refs`) | **admitted** (exit 0) | Owner signed off; authority warranted. |
| `proposed` | `false` (`authority_refs: []`) | **review-required** (exit 3) | Visible and tracked, but **NOT authorized**. Awaiting human owner sign-off. |
| `denied` / `revoked` | `false` | **deny** (exit 1) | Fail-closed. |
| *(no entry at all)* | — | **deny** (exit 1) | Invisible authority — the INV-ACC-1 violation. |

## What is (and is not) in this PR

- `example-admitted-agent.admission.json` — a **benign fixture** proving the
  gate's admitted (pass) path. Not a dangerous agent.
- The remaining entries are **PROPOSED stubs** for the priority
  destructive/offensive subset of the 46 invisible-authority agents from
  `prophet-core-catalog` `ds.agents-manifests` (verbs `kill.agent`,
  `policy.evaluate`, `quorum.vote`, `exec.command`; SCOPE-D exploit/enum
  subagents; the Splunk MCP `cmd:bash` surface).

**These proposed stubs do NOT grant authority.** `authority.granted` is `false`
and `authority_refs` is empty by construction; the schema forbids a
proposed/denied/revoked manifest from claiming granted authority or production
admission. Authorizing any of these is the **owner's** decision: set
`admission_status: admitted`, `authority.granted: true`, populate
`authority.authority_refs` with the warranting owner/grant/policy/control/evidence
refs, and record `authority.sign_off`. The gate will only then exit 0 for them.

Adding a new agent to the registry: drop a `<name>.admission.json` here
(schema above), start it `proposed`, run
`make validate-fail-closed-admission-gate`, and hand it to the owning repo for
sign-off.
