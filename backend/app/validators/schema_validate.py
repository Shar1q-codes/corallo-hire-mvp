from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from app.validators.failure import ValidationFailure
from app.validators.types import FailureCode, RoleType

_SCHEMA_BY_ROLE: dict[RoleType, str] = {
    RoleType.INTENT: "intent_alignment_v1.json",
    RoleType.RISK: "risk_signals_v1.json",
    RoleType.ASSUMPTION: "assumption_register_v1.json",
    RoleType.INTERVIEW: "interview_guidance_v1.json",
}


def _schema_path(role: RoleType) -> Path:
    return Path(__file__).resolve().parents[1] / "schemas_json" / _SCHEMA_BY_ROLE[role]


def _pointer(path: list) -> str:
    if not path:
        return "/"
    return "/" + "/".join(str(p) for p in path)


def validate_schema(role: RoleType, payload: dict) -> ValidationFailure | None:
    schema = json.loads(_schema_path(role).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda err: list(err.path))
    if not errors:
        return None

    first = errors[0]
    return ValidationFailure(
        code=FailureCode.SCHEMA_INVALID,
        message=f"Schema validation failed: {first.message}",
        paths=[_pointer(list(first.path))],
        raw_excerpt=str(first.instance)[:200],
    )

