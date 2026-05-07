.PHONY: validate test release-dry-run ops-history-grants-validate validate-superconscious-reasoning-grant

validate: ops-history-grants-validate validate-superconscious-reasoning-grant
	python3 tools/validate_agent_registry_examples.py

ops-history-grants-validate:
	python3 tools/validate_ops_history_agent_grants.py

validate-superconscious-reasoning-grant:
	python3 tools/validate_superconscious_reasoning_grant.py

test:
	python3 -m pytest -q tools/tests

release-dry-run:
	python3 tools/release_dry_run.py
