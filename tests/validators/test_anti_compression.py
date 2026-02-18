import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.validators.anti_compression import validate_anti_compression  # noqa: E402
from app.validators.types import FailureCode  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_anti_compression_flags_overall_language() -> None:
    payload = _load("invalid_risks_summary.json")
    failure = validate_anti_compression(payload)
    assert failure is not None
    assert failure.code == FailureCode.ANTI_COMPRESSION_FAIL
    assert any("overall" in match.lower() for match in failure.matches)

