.PHONY: validate validate-workspace-ops test release-dry-run

validate:
	python3 tools/validate_agent_registry_examples.py
	python3 tools/validate_workspace_operation_records.py

validate-workspace-ops:
	python3 tools/validate_workspace_operation_records.py

test:
	python3 -m pytest -q tools/tests

release-dry-run:
	python3 tools/release_dry_run.py
