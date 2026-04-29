.PHONY: validate test

validate:
	python3 tools/validate_agent_registry_examples.py

test:
	python3 -m pytest -q tools/tests
