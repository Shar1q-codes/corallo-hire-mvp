from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.validators.excerpt import validate_excerpt_resistance  # noqa: E402
from app.validators.types import FailureCode  # noqa: E402


def test_excerpt_resistance_fails_when_two_or_more_sampled_sentences_are_verdict_like() -> None:
    payload = {
        "text_a": "We should hire immediately based on this statement.",
        "text_b": "Do not hire if one metric is missing.",
        "text_c": "This sentence is neutral and descriptive."
    }
    failure = validate_excerpt_resistance(payload, seed=42)
    assert failure is not None
    assert failure.code == FailureCode.EXCERPT_RESISTANCE_FAIL
