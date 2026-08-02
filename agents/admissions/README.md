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
- The remaining 9 entries are the priority **destructive/offensive** subset of
  the 46 invisible-authority agents from `prophet-core-catalog`
  `ds.agents-manifests` (verbs `kill.agent`, `policy.evaluate`, `quorum.vote`,
  `exec.command`; SCOPE-D exploit/enum subagents; the Splunk MCP `cmd:bash`
  surface). They were first landed as `proposed` stubs (visible but
  unauthorized) and are now **`admitted`** following owner sign-off.

**Owner sign-off (2026-08-02).** Lord Michael (owner) approved all 9 — a **real
but verbal, in-session** approval, recorded honestly (not as a formal signed
document) in `governance/owner-signoffs/2026-08-02-agent-admissions.json`. Each
admission is now `admission_status: admitted`, `authority.granted: true`, with
`authority.authority_refs` populated with the warranting owner grant, the
governing Standard 030 / trustops policy, the owner sign-off evidence
(`evidence://agent-registry/owner-signoff/2026-08-02-agent-admissions`, which
resolves to that record file), and — for this destructive/offensive class — a
**containment ref** (`policy://containment/…`), plus `authority.sign_off`
recording the approval.

**Containment is real and enforced, not nominal.** Every `policy://containment/…`
ref resolves to a real, schema-validated policy file under
`governance/containment/` with **enforceable terms** (non-prod only, sandbox
required, human-in-the-loop, quorum for `kill.agent`, single-namespace,
deny-by-default). The runtime authorize gate enforces this: for a
destructive/offensive agent it **denies** the action unless (a) the named
containment policy file resolves AND (b) its conditions are satisfied by the
action context. A containment ref that does not resolve is a fail-closed deny —
so a "policy that says contained" cannot pass as governed.

**Admission is not omnipotence.** Admission makes the agent VISIBLE + admitted
so the runtime authorize surface (`tools/authorize.py`) can govern it; it does
NOT hand it unconditional authority. The per-action authority state, the
containment gate, and the fail-closed authorize gate each govern the action. The
permanent fail-closed teeth remain: a capability-bearing agent with **no**
admission entry (`unadmitted-capability-agent.invalid.json`) is still denied
(`invisible_authority_no_admission_entry`).

To authorize a new agent, the **owner** sets `admission_status: admitted`,
`authority.granted: true`, populates `authority.authority_refs` with the
warranting owner/grant/policy/control/evidence (and, for the destructive class, a
containment) refs, and records `authority.sign_off`. The gate exits 0 only then.

Adding a new agent to the registry: drop a `<name>.admission.json` here
(schema above), start it `proposed`, run
`make validate-fail-closed-admission-gate`, and hand it to the owning repo for
sign-off.
