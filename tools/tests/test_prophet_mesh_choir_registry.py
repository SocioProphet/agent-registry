import json
from pathlib import Path

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from validate_prophet_mesh_choir_registry import validate

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "contracts/prophet-mesh/prophet-mesh-choir-registry.v0.1.json"


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_prophet_mesh_choir_registry_validates():
    errors = validate(_load_fixture())
    assert errors == []


def test_prophet_mesh_choir_registry_rejects_missing_default_agent():
    data = _load_fixture()
    data["agents"] = [agent for agent in data["agents"] if agent["id"] != "writing-agent"]
    errors = validate(data)
    assert any("required default agent missing" in error for error in errors)


def test_prophet_mesh_choir_registry_rejects_unscoped_memory():
    data = _load_fixture()
    data["agents"][0]["allowed_memory_scopes"].append("unscoped")
    errors = validate(data)
    assert any("forbidden memory scopes" in error for error in errors)


def test_prophet_mesh_choir_registry_rejects_missing_required_control():
    data = _load_fixture()
    data["agents"][1]["required_controls"] = ["identity", "policy", "evidence"]
    errors = validate(data)
    assert any("missing required controls" in error for error in errors)
