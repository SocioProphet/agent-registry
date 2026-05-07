.PHONY: validate test release-dry-run validate-superconscious-reasoning-grant

validate: validate-superconscious-reasoning-grant
	python3 tools/validate_agent_registry_examples.py

validate-superconscious-reasoning-grant:
	python3 tools/validate_superconscious_reasoning_grant.py

test:
	python3 -m pytest -q tools/tests

release-dry-run:
	python3 tools/release_dry_run.py
