from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.validators.bundle import ValidationPipeline  # noqa: E402
from app.validators.types import FailureCode, RoleType  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"
GOOD_FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "validators" / "fixtures"


def test_score_probability_fixture_fails() -> None:
    pipeline = ValidationPipeline()
    raw = (FIXTURES / "bad_output_contains_score.json").read_text(encoding="utf-8")
    result = pipeline.validate(RoleType.RISK, raw)
    assert result.code == FailureCode.PROBABILITY_LANGUAGE


def test_good_risk_fixture_passes() -> None:
    pipeline = ValidationPipeline()
    raw = (GOOD_FIXTURES / "valid_risks.json").read_text(encoding="utf-8")
    result = pipeline.validate(RoleType.RISK, raw)
    assert isinstance(result, dict)
    assert "risks" in result

