from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.validators.bundle import ValidationPipeline  # noqa: E402
from app.validators.failure import ValidationFailure  # noqa: E402
from app.validators.types import FailureCode, RoleType  # noqa: E402


def test_pipeline_stops_after_json_parse_failure() -> None:
    calls: list[str] = []

    def parse_fn(_raw: str):
        calls.append("parse")
        return ValidationFailure(code=FailureCode.JSON_PARSE_ERROR, message="bad json")

    def schema_fn(_role, _payload):
        calls.append("schema")
        return None

    pipeline = ValidationPipeline(parse_fn=parse_fn, schema_fn=schema_fn)
    result = pipeline.validate(RoleType.INTENT, "bad input")
    assert isinstance(result, ValidationFailure)
    assert result.code == FailureCode.JSON_PARSE_ERROR
    assert calls == ["parse"]


def test_pipeline_order_is_strict() -> None:
    calls: list[str] = []

    def parse_fn(_raw: str):
        calls.append("parse")
        return {"hypotheses": []}

    def schema_fn(_role, _payload):
        calls.append("schema")
        return None

    def language_fn(_role, _payload):
        calls.append("language")
        return None

    def anti_fn(_payload):
        calls.append("anti")
        return None

    def excerpt_fn(_payload):
        calls.append("excerpt")
        return None

    pipeline = ValidationPipeline(
        parse_fn=parse_fn,
        schema_fn=schema_fn,
        language_fn=language_fn,
        anti_compression_fn=anti_fn,
        excerpt_fn=excerpt_fn,
    )
    result = pipeline.validate(RoleType.INTENT, "{}")
    assert isinstance(result, dict)
    assert calls == ["parse", "schema", "language", "anti", "excerpt"]


def test_pipeline_fail_closed_returns_first_failure_only() -> None:
    def parse_fn(_raw: str):
        return {"risks": []}

    def schema_fn(_role, _payload):
        return ValidationFailure(code=FailureCode.SCHEMA_INVALID, message="missing fields")

    def language_fn(_role, _payload):
        return ValidationFailure(code=FailureCode.FORBIDDEN_LANGUAGE, message="forbidden")

    pipeline = ValidationPipeline(parse_fn=parse_fn, schema_fn=schema_fn, language_fn=language_fn)
    result = pipeline.validate(RoleType.RISK, "{}")
    assert isinstance(result, ValidationFailure)
    assert result.code == FailureCode.SCHEMA_INVALID


def test_validate_with_attempts_limits_to_two_attempts() -> None:
    calls: list[str] = []

    def parse_fn(raw: str):
        calls.append(raw)
        return ValidationFailure(code=FailureCode.JSON_PARSE_ERROR, message="bad")

    pipeline = ValidationPipeline(parse_fn=parse_fn)
    result = pipeline.validate_with_attempts(RoleType.INTENT, ["a1", "a2", "a3"], max_attempts=2)
    assert isinstance(result, ValidationFailure)
    assert result.code == FailureCode.JSON_PARSE_ERROR
    assert calls == ["a1", "a2"]
