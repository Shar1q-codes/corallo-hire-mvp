from __future__ import annotations

import json

from app.validators.failure import ValidationFailure
from app.validators.types import FailureCode


def parse_json_object(raw_text: str) -> dict | ValidationFailure:
    decoder = json.JSONDecoder()

    for index, char in enumerate(raw_text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(raw_text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
        return ValidationFailure(
            code=FailureCode.JSON_PARSE_ERROR,
            message="Parsed JSON is not an object.",
            raw_excerpt=raw_text[index : index + 200],
        )

    return ValidationFailure(
        code=FailureCode.JSON_PARSE_ERROR,
        message="Unable to parse JSON object from text.",
        raw_excerpt=raw_text[:200],
    )

