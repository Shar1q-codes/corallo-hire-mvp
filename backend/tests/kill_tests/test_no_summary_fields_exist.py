import json
from pathlib import Path
import sys
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.validators.bundle import ValidationPipeline  # noqa: E402
from app.validators.types import FailureCode, RoleType  # noqa: E402

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "backend" / "app" / "schemas_json"
FIXTURE_DIR = Path(__file__).parent / "fixtures"
FORBIDDEN_KEYS = {"summary", "overall", "recommendation", "score", "rank"}


def _collect_keys(node: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(str(key).lower())
            keys.update(_collect_keys(value))
    elif isinstance(node, list):
        for value in node:
            keys.update(_collect_keys(value))
    return keys


def test_schemas_contain_no_summary_or_ranking_fields() -> None:
    for schema_path in SCHEMA_DIR.glob("*.json"):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        keys = _collect_keys(schema)
        assert FORBIDDEN_KEYS.isdisjoint(keys), f"Forbidden field found in {schema_path.name}"


def test_bad_summary_fixture_fails_validation() -> None:
    pipeline = ValidationPipeline()
    raw = (FIXTURE_DIR / "bad_output_contains_overall_summary.json").read_text(encoding="utf-8")
    result = pipeline.validate(RoleType.INTERVIEW, raw)
    assert result.code in {FailureCode.SCHEMA_INVALID, FailureCode.ANTI_COMPRESSION_FAIL}
