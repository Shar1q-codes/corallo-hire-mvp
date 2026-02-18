import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.validators.bundle import ValidationPipeline  # noqa: E402
from app.validators.failure import ValidationFailure  # noqa: E402
from app.validators.repair import build_repair_instruction  # noqa: E402
from app.validators.types import FailureCode, RoleType  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
GOOD_FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "validators" / "fixtures"


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_forbidden_language_fixture_fails() -> None:
    pipeline = ValidationPipeline()
    result = pipeline.validate(RoleType.INTENT, _load(FIXTURES / "bad_output_contains_hire.json"))
    assert result.code == FailureCode.FORBIDDEN_LANGUAGE


def test_good_intent_fixture_passes() -> None:
    pipeline = ValidationPipeline()
    result = pipeline.validate(RoleType.INTENT, _load(GOOD_FIXTURES / "valid_intent.json"))
    assert isinstance(result, dict)
    assert "hypotheses" in result


def test_repair_instruction_avoids_outcome_terms() -> None:
    failure = ValidationFailure(
        code=FailureCode.FORBIDDEN_LANGUAGE,
        message="forbidden",
        matches=["hire"],
    )
    instruction = build_repair_instruction(failure).lower()
    assert "hire" not in instruction
    assert "reject" not in instruction
