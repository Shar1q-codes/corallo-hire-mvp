import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.validators.language import validate_language  # noqa: E402
from app.validators.types import FailureCode, RoleType  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_language_validator_catches_forbidden_nested_wording() -> None:
    payload = _load("invalid_intent_forbidden_language.json")
    failure = validate_language(RoleType.INTENT, payload)
    assert failure is not None
    assert failure.code == FailureCode.FORBIDDEN_LANGUAGE
    assert any("best" in match.lower() or "fit" in match.lower() for match in failure.matches)


def test_language_validator_catches_risk_statement_without_arrow() -> None:
    payload = _load("valid_risks.json")
    payload["risks"][0]["risk_statement"] = "Mechanism and failure mode are both described but not linked"
    failure = validate_language(RoleType.RISK, payload)
    assert failure is not None
    assert failure.code == FailureCode.RISK_NAMING_INVALID


def test_language_validator_catches_probability_language() -> None:
    payload = _load("valid_assumptions.json")
    payload["assumptions"][0]["confidence_rationale"] = "There is 70% probability this pattern will hold."
    failure = validate_language(RoleType.ASSUMPTION, payload)
    assert failure is not None
    assert failure.code == FailureCode.PROBABILITY_LANGUAGE

