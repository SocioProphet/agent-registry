from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make the validators in tools/ importable regardless of pytest collection order.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_bmg_layer_gate import ValidationError, main, validate_record  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "bmg-layer-gate"


def _load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_canonical_example_validates() -> None:
    assert main() == 0


def test_layer1_autonomous_is_allowed() -> None:
    # The canonical behavioural example: within-manifest, autonomous, no signoff.
    from validate_bmg_layer_gate import EXAMPLE, load

    validate_record(load(EXAMPLE))  # must not raise


def test_layer2_with_signoff_is_allowed() -> None:
    validate_record(_load("architectural-signed.example.json"))  # must not raise


def test_layer2_autonomous_is_rejected() -> None:
    # BMG-1: architectural actions are never autonomous and require sign-off.
    with pytest.raises(ValidationError):
        validate_record(_load("architectural-autonomous.invalid.json"))


def test_behavioural_altering_future_actions_is_rejected() -> None:
    # BMG-1 core invariant: altering the permissible-future-action set is Layer-2,
    # so a 'behavioural' record that does so must fail closed.
    with pytest.raises(ValidationError):
        validate_record(_load("behavioural-alters-future.invalid.json"))


def test_missing_signoff_on_architectural_is_rejected() -> None:
    rec = _load("architectural-signed.example.json")
    rec["humanSignoff"] = None
    with pytest.raises(ValidationError):
        validate_record(rec)


def test_unexpected_fields_are_rejected() -> None:
    # Fail-closed parity with the schema's additionalProperties:false.
    top = _load("architectural-signed.example.json")
    top["surpriseField"] = "nope"
    with pytest.raises(ValidationError):
        validate_record(top)

    nested = _load("architectural-signed.example.json")
    nested["effects"]["surprise"] = True
    with pytest.raises(ValidationError):
        validate_record(nested)

    so = _load("architectural-signed.example.json")
    so["humanSignoff"]["surprise"] = "x"
    with pytest.raises(ValidationError):
        validate_record(so)


def test_invalid_fixtures_are_named_invalid() -> None:
    # Guardrail: every *.invalid.json under the example dir must actually be rejected.
    invalid = sorted(EXAMPLES.glob("*.invalid.json"))
    assert invalid, "expected at least one .invalid.json fixture"
    for path in invalid:
        with pytest.raises(ValidationError):
            validate_record(json.loads(path.read_text(encoding="utf-8")))
