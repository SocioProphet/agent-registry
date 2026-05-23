#!/usr/bin/env python3
"""Read-only AgentAuthorityCurrentState lookup helper.

This command resolves a validated AgentAuthorityCurrentState record from an
explicit state file or from a local source directory. It never derives authority
state from raw TrustOps receipts and never mutates authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import validate_authority_state_contracts

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "contracts" / "trustops"
NON_GOALS = [
    "authority_mutation",
    "restoration_approval",
    "raw_receipt_to_authority_state_derivation",
    "agentplane_admission",
    "runtime_execution",
]


class LookupError(Exception):
    def __init__(self, reason_code: str, message: str):
        self.reason_code = reason_code
        self.message = message
        super().__init__(message)


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def load_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LookupError("state_file_missing", f"state file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LookupError("state_file_invalid_json", f"state file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise LookupError("state_file_not_object", f"state file must contain a JSON object: {path}")
    return data


def validate_state(record: dict[str, Any]) -> None:
    try:
        validate_authority_state_contracts.validate_state(record)
    except validate_authority_state_contracts.ValidationError as exc:
        raise LookupError("authority_state_invalid", str(exc)) from exc


def state_result(record: dict[str, Any], source_path: Path) -> dict[str, Any]:
    return {
        "schemaVersion": "agent-registry.authority-state-lookup.v0.1",
        "recordType": "AgentAuthorityStateLookupResult",
        "ok": True,
        "mode": "readonly",
        "agentRef": record["agentRef"],
        "authority_status": record["authority_status"],
        "stateId": record["stateId"],
        "state_file": str(source_path),
        "authority_state": record,
        "non_goals": NON_GOALS,
    }


def error_result(reason_code: str, message: str, *, agent_ref: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schemaVersion": "agent-registry.authority-state-lookup.v0.1",
        "recordType": "AgentAuthorityStateLookupError",
        "ok": False,
        "mode": "readonly",
        "reason_code": reason_code,
        "message": message,
        "non_goals": NON_GOALS,
    }
    if agent_ref:
        payload["agentRef"] = agent_ref
    return payload


def load_validated_state(path: Path) -> dict[str, Any]:
    record = load_object(path)
    validate_state(record)
    return record


def candidate_files(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        return []
    return sorted(source_dir.glob("agent-authority-current-state.*.json"))


def find_state(source_dir: Path, agent_ref: str, status: str | None) -> tuple[dict[str, Any], Path]:
    matches: list[tuple[dict[str, Any], Path]] = []
    errors: list[str] = []
    for path in candidate_files(source_dir):
        try:
            record = load_validated_state(path)
        except LookupError as exc:
            errors.append(f"{path}: {exc.message}")
            continue
        if record.get("agentRef") != agent_ref:
            continue
        if status and record.get("authority_status") != status:
            continue
        matches.append((record, path))

    if not matches:
        detail = f"no authority state found for {agent_ref}"
        if status:
            detail += f" with status {status}"
        if errors:
            detail += f"; skipped invalid states: {'; '.join(errors)}"
        raise LookupError("authority_state_not_found", detail)
    if len(matches) > 1:
        refs = ", ".join(record["stateId"] for record, _path in matches)
        raise LookupError("authority_state_ambiguous", f"multiple authority states matched {agent_ref}: {refs}")
    return matches[0]


def command_get(args: argparse.Namespace) -> int:
    try:
        if args.state_file:
            path = Path(args.state_file)
            record = load_validated_state(path)
            if record.get("agentRef") != args.agent_ref:
                raise LookupError(
                    "authority_state_agent_mismatch",
                    f"state file agentRef {record.get('agentRef')} does not match requested {args.agent_ref}",
                )
            if args.status and record.get("authority_status") != args.status:
                raise LookupError(
                    "authority_state_status_mismatch",
                    f"state file status {record.get('authority_status')} does not match requested {args.status}",
                )
        else:
            record, path = find_state(Path(args.source_dir), args.agent_ref, args.status)
        emit(state_result(record, path))
        return 0
    except LookupError as exc:
        emit(error_result(exc.reason_code, exc.message, agent_ref=args.agent_ref))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="authority-state-lookup")
    sub = parser.add_subparsers(dest="command", required=True)

    get = sub.add_parser("get", help="Resolve a validated AgentAuthorityCurrentState record.")
    get.add_argument("agent_ref")
    get.add_argument("--status", choices=["active", "reduced", "suspended", "revoked"])
    get.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    get.add_argument("--state-file")
    get.set_defaults(func=command_get)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
