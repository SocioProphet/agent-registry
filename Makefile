.PHONY: validate validate-workspace-ops test release-dry-run ops-history-grants-validate validate-superconscious-reasoning-grant validate-trustops-agent-authority-decision validate-authority-state-contracts

validate: ops-history-grants-validate validate-superconscious-reasoning-grant validate-workspace-ops validate-trustops-agent-authority-decision validate-authority-state-contracts
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

test:
	python3 -m pytest -q tools/tests

release-dry-run:
	python3 tools/release_dry_run.py
