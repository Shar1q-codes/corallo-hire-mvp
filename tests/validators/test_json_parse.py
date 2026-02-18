from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.validators.json_parse import parse_json_object  # noqa: E402
from app.validators.types import FailureCode  # noqa: E402


def test_parse_json_extracts_first_object_from_wrapped_text() -> None:
    raw = "preface text\n{\"a\": 1, \"b\": {\"c\": true}}\ntrailing text"
    parsed = parse_json_object(raw)
    assert isinstance(parsed, dict)
    assert parsed["a"] == 1


def test_parse_json_failure_returns_code() -> None:
    parsed = parse_json_object("not json at all")
    assert parsed.code == FailureCode.JSON_PARSE_ERROR

