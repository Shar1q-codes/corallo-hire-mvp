import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.validators.schema_validate import validate_schema  # noqa: E402
from app.validators.types import FailureCode, RoleType  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_schema_validation_passes_all_valid_fixtures() -> None:
    assert validate_schema(RoleType.INTENT, _load("valid_intent.json")) is None
    assert validate_schema(RoleType.RISK, _load("valid_risks.json")) is None
    assert validate_schema(RoleType.ASSUMPTION, _load("valid_assumptions.json")) is None
    assert validate_schema(RoleType.INTERVIEW, _load("valid_interview_guidance.json")) is None


def test_schema_validation_fails_missing_required_field() -> None:
    payload = _load("valid_intent.json")
    del payload["hypotheses"][0]["counter_signals"]
    failure = validate_schema(RoleType.INTENT, payload)
    assert failure is not None
    assert failure.code == FailureCode.SCHEMA_INVALID

