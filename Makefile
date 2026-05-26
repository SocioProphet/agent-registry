.PHONY: validate validate-workspace-ops test release-dry-run ops-history-grants-validate validate-superconscious-reasoning-grant validate-trustops-agent-authority-decision validate-authority-state-contracts validate-authority-state-lookup validate-workspace-context-authority-binding validate-control-plane-capability-grant

validate: ops-history-grants-validate validate-superconscious-reasoning-grant validate-workspace-ops validate-trustops-agent-authority-decision validate-authority-state-contracts validate-authority-state-lookup validate-workspace-context-authority-binding validate-control-plane-capability-grant
	python3 tools/validate_agent_registry_examples.py

validate-workspace-ops:
	python3 tools/validate_workspace_operation_records.py

ops-history-grants-validate:
	python3 tools/validate_ops_history_agent_grants.py

validate-superconscious-reasoning-grant:
	python3 tools/validate_superconscious_reasoning_grant.py

validate-trustops-agent-authority-decision:
	python3 -m json.tool contracts/trustops/agent-authority-decision.v0.1.schema.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-decision.v0.1.example.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-decision.pass-revoked.invalid.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-decision.missing-decision-authority.invalid.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-decision.require-review-unchanged.invalid.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-decision.revoke-reduced.invalid.json >/dev/null
	python3 tools/validate_trustops_agent_authority_decision.py

validate-authority-state-contracts:
	python3 -m json.tool contracts/trustops/agent-authority-current-state.v0.1.schema.json >/dev/null
	python3 -m json.tool contracts/trustops/authority-restoration-decision.v0.1.schema.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-current-state.active.example.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-current-state.reduced.example.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-current-state.suspended.example.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-current-state.revoked.example.json >/dev/null
	python3 -m json.tool contracts/trustops/agent-authority-current-state.raw-receipt.invalid.json >/dev/null
	python3 -m json.tool contracts/trustops/authority-restoration-decision.restore.example.json >/dev/null
	python3 -m json.tool contracts/trustops/authority-restoration-decision.missing-authorization.invalid.json >/dev/null
	python3 tools/validate_authority_state_contracts.py

validate-authority-state-lookup:
	python3 tools/authority_state_lookup.py get agent-registry://agent-alpha --status active >/tmp/agent-registry-authority-active.json
	python3 tools/authority_state_lookup.py get agent-registry://agent-alpha --state-file contracts/trustops/agent-authority-current-state.suspended.example.json >/tmp/agent-registry-authority-suspended.json
	! python3 tools/authority_state_lookup.py get agent-registry://agent-alpha --state-file contracts/trustops/agent-authority-current-state.raw-receipt.invalid.json >/tmp/agent-registry-authority-invalid.json

validate-workspace-context-authority-binding:
	python3 -m json.tool contracts/workspace-context/workspace-context-authority-binding.v0.1.schema.json >/dev/null
	python3 -m json.tool contracts/workspace-context/workspace-context-authority-binding.v0.1.example.json >/dev/null
	python3 tools/validate_workspace_context_authority_binding.py

validate-control-plane-capability-grant:
	python3 -m json.tool contracts/control-plane/control-plane-capability-grant.v0.1.schema.json >/dev/null
	python3 -m json.tool contracts/control-plane/control-plane-capability-grant.v0.1.example.json >/dev/null
	python3 tools/validate_control_plane_capability_grant.py

test:
	python3 -m pytest -q tools/tests

release-dry-run:
	python3 tools/release_dry_run.py
