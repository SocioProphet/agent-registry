# TrustOps Authority State Lookup v0

## Purpose

`tools/authority_state_lookup.py` provides a read-only lookup surface for `AgentAuthorityCurrentState` records.

It exists so AgentPlane and other consumers can resolve current authority posture without reconstructing state from raw TrustOps receipts.

## Command

Lookup by agent ref and status from the local authority-state source directory:

```bash
python3 tools/authority_state_lookup.py get agent-registry://agent-alpha --status active
```

Lookup from an explicit validated state file:

```bash
python3 tools/authority_state_lookup.py get agent-registry://agent-alpha \
  --state-file contracts/trustops/agent-authority-current-state.suspended.example.json
```

## Output

Successful lookup emits:

```text
recordType = AgentAuthorityStateLookupResult
ok = true
mode = readonly
authority_state = AgentAuthorityCurrentState
```

Failed lookup emits:

```text
recordType = AgentAuthorityStateLookupError
ok = false
mode = readonly
reason_code = <fail-closed reason>
```

## Fail-closed reasons

The lookup can fail closed with:

- `state_file_missing`
- `state_file_invalid_json`
- `state_file_not_object`
- `authority_state_invalid`
- `authority_state_not_found`
- `authority_state_ambiguous`
- `authority_state_agent_mismatch`
- `authority_state_status_mismatch`

## Authority derivation boundary

Lookup returns validated `AgentAuthorityCurrentState` only.

It does not derive current authority state from:

```text
trustops-receipt:*
```

Raw TrustOps receipts are evidence, not authority mutation.

Current authority state must derive from explicit authority decisions or restoration decisions, as enforced by `tools/validate_authority_state_contracts.py`.

## AgentPlane consumption

AgentPlane governed-runner admission should consume the lookup result's embedded `authority_state` field as the authority input for `AttemptAdmissionReceipt` construction.

AgentPlane must not compute, mutate, or restore authority state.

## Validation

```bash
make validate-authority-state-lookup
python3 -m pytest -q tools/tests/test_authority_state_lookup.py
```

The tests cover:

- active authority lookup by status;
- explicit state-file lookup;
- ambiguous lookup fail-closed;
- missing state fail-closed;
- raw-receipt-derived state rejection;
- agent-ref mismatch fail-closed.

## Non-goals

This lookup does not:

- mutate authority;
- approve restoration;
- derive authority state from raw receipts;
- emit AgentPlane admission receipts;
- execute agents;
- run safety preflight;
- settle budget.
