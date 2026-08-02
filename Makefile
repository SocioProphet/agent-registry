.PHONY: validate validate-workspace-ops test release-dry-run ops-history-grants-validate validate-superconscious-reasoning-grant validate-trustops-agent-authority-decision validate-authority-state-contracts validate-authority-state-lookup validate-workspace-context-authority-binding validate-control-plane-capability-grant validate-agent-wall-context validate-fraud-agent-admission-profile validate-trust-chain-agent-manifest-binding validate-prophet-mesh-choir-registry validate-agent-authority-authorize validate-bmg-layer-gate validate-fail-closed-admission-gate

validate: ops-history-grants-validate validate-superconscious-reasoning-grant validate-workspace-ops validate-trustops-agent-authority-decision validate-authority-state-contracts validate-authority-state-lookup validate-workspace-context-authority-binding validate-control-plane-capability-grant validate-agent-wall-context validate-fraud-agent-admission-profile validate-trust-chain-agent-manifest-binding validate-prophet-mesh-choir-registry validate-agent-authority-authorize validate-bmg-layer-gate validate-fail-closed-admission-gate
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

validate-bmg-layer-gate:
	python3 -m json.tool contracts/control-plane/bmg-layer-gate.v0.1.schema.json >/dev/null
	python3 -m json.tool contracts/control-plane/bmg-layer-gate.v0.1.example.json >/dev/null
	python3 -m json.tool examples/bmg-layer-gate/architectural-signed.example.json >/dev/null
	python3 -m json.tool examples/bmg-layer-gate/architectural-autonomous.invalid.json >/dev/null
	python3 -m json.tool examples/bmg-layer-gate/behavioural-alters-future.invalid.json >/dev/null
	python3 tools/validate_bmg_layer_gate.py

validate-agent-wall-context:
	python3 -m json.tool contracts/wallguard/agent-wall-context.v0.1.schema.json >/dev/null
	python3 -m json.tool contracts/wallguard/agent-wall-context.active.example.json >/dev/null
	python3 -m json.tool contracts/wallguard/agent-wall-context.revoked-invalid.json >/dev/null
	python3 -m json.tool contracts/wallguard/agent-wall-context.contaminated-global-invalid.json >/dev/null
	python3 tools/validate_agent_wall_context.py

validate-fraud-agent-admission-profile:
	python3 -m json.tool schemas/fraud-agent-admission-profile.v0.1.schema.json >/dev/null
	python3 -m json.tool examples/fraud-agent-admission-profile.report-only.example.json >/dev/null
	python3 -m json.tool examples/fraud-agent-admission-profile.human-impact-no-policy.invalid.json >/dev/null
	python3 -m json.tool examples/fraud-agent-admission-profile.memory-writeback-unreviewed.invalid.json >/dev/null
	python3 tools/validate_fraud_agent_admission_profile.py

validate-trust-chain-agent-manifest-binding:
	python3 -m json.tool schemas/trust-chain-agent-manifest-binding.v0.1.schema.json >/dev/null
	python3 -m json.tool examples/trust-chain-agent-manifest-binding.preview.example.json >/dev/null
	python3 -m json.tool examples/trust-chain-agent-manifest-binding.blocked.json >/dev/null
	python3 tools/validate_trust_chain_agent_manifest_binding.py

validate-prophet-mesh-choir-registry:
	python3 -m json.tool contracts/prophet-mesh/prophet-mesh-choir-registry.v0.1.json >/dev/null
	python3 tools/validate_prophet_mesh_choir_registry.py

validate-agent-authority-authorize:
	# allow: active + unchanged dimension exits 0
	python3 tools/authorize.py check agent-registry://agent-alpha --action tool --state-file contracts/trustops/agent-authority-current-state.active.example.json >/dev/null
	# fail-closed: revoked authority denies (nonzero) and never authorizes
	! python3 tools/authorize.py check agent-registry://agent-alpha --action autonomous --state-file contracts/trustops/agent-authority-current-state.revoked.example.json >/dev/null
	# fail-closed: an invalid (raw-receipt) state denies (nonzero)
	! python3 tools/authorize.py check agent-registry://agent-alpha --action tool --state-file contracts/trustops/agent-authority-current-state.raw-receipt.invalid.json >/dev/null
	# NOTE: the pytest suite for this surface runs under `make test` (validate.yml
	# installs pytest); this target stays stdlib-only so it also passes in the
	# release-dry-run job, which runs `make validate` without pytest.

validate-fail-closed-admission-gate:
	# Schemas and fixtures are well-formed JSON.
	python3 -m json.tool schemas/agent-admission-manifest.v0.1.schema.json >/dev/null
	python3 -m json.tool examples/admission-gate/unadmitted-capability-agent.invalid.json >/dev/null
	for f in agents/admissions/*.admission.json; do python3 -m json.tool "$$f" >/dev/null; done
	for f in examples/admission-gate/declared/*.json; do python3 -m json.tool "$$f" >/dev/null; done
	# INV-ACC-1 teeth, both ways (Standard 030):
	# pass: a capability-bearing agent WITH a resolvable, granted admission entry.
	python3 tools/fail_closed_admission_gate.py check examples/admission-gate/declared/example-admitted-agent.declared.json >/dev/null
	# fail-closed: capability declared with NO admission entry denies (nonzero) -> invisible authority.
	! python3 tools/fail_closed_admission_gate.py check examples/admission-gate/unadmitted-capability-agent.invalid.json >/dev/null
	# fail-closed: a PROPOSED dangerous stub is review-required, never auto-authorized (nonzero).
	! python3 tools/fail_closed_admission_gate.py check examples/admission-gate/declared/agent-governor-001.declared.json >/dev/null
	# fail-closed: scanning the priority population holds every proposed/unadmitted agent below admitted (nonzero).
	! python3 tools/fail_closed_admission_gate.py scan examples/admission-gate/declared >/dev/null
	# NOTE: the pytest suite for this surface runs under `make test`; this target
	# stays stdlib-only so it also passes in the release-dry-run job (no pytest).

test:
	python3 -m pytest -q tools/tests

release-dry-run:
	python3 tools/release_dry_run.py
