from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.validators.excerpt import validate_excerpt_resistance  # noqa: E402
from app.validators.types import FailureCode  # noqa: E402


def test_excerpt_resistance_flags_verdict_like_sentences() -> None:
    payload = {
        "focus_areas": [
            {
                "objective_statement": "We should hire immediately based on this short statement.",
                "linked_signals": ["This is the top profile and should be advanced directly."],
                "why_it_matters": "Decision language appears in this sentence.",
                "signals_increasing_confidence": ["Another sentence with verdict language."],
                "signals_decreasing_confidence": ["Neutral sentence retained for control."]
            }
        ]
    }
    failure = validate_excerpt_resistance(payload, seed=42)
    assert failure is not None
    assert failure.code == FailureCode.EXCERPT_RESISTANCE_FAIL

