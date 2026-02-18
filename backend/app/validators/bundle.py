from __future__ import annotations

from collections.abc import Callable

from app.validators.anti_compression import validate_anti_compression
from app.validators.excerpt import validate_excerpt_resistance
from app.validators.failure import ValidationFailure
from app.validators.json_parse import parse_json_object
from app.validators.language import validate_language
from app.validators.schema_validate import validate_schema
from app.validators.types import FailureCode, RoleType


class ValidationPipeline:
    def __init__(
        self,
        *,
        parse_fn: Callable[[str], dict | ValidationFailure] = parse_json_object,
        schema_fn: Callable[[RoleType, dict], ValidationFailure | None] = validate_schema,
        language_fn: Callable[[RoleType, dict], ValidationFailure | None] = validate_language,
        anti_compression_fn: Callable[[dict], ValidationFailure | None] = validate_anti_compression,
        excerpt_fn: Callable[[dict], ValidationFailure | None] = validate_excerpt_resistance,
    ) -> None:
        self.parse_fn = parse_fn
        self.schema_fn = schema_fn
        self.language_fn = language_fn
        self.anti_compression_fn = anti_compression_fn
        self.excerpt_fn = excerpt_fn

    def validate(self, role: RoleType, raw_text: str) -> dict | ValidationFailure:
        parsed = self.parse_fn(raw_text)
        if isinstance(parsed, ValidationFailure):
            return parsed

        schema_failure = self.schema_fn(role, parsed)
        if schema_failure:
            return schema_failure

        language_failure = self.language_fn(role, parsed)
        if language_failure:
            return language_failure

        anti_compression_failure = self.anti_compression_fn(parsed)
        if anti_compression_failure:
            return anti_compression_failure

        excerpt_failure = self.excerpt_fn(parsed)
        if excerpt_failure:
            return excerpt_failure

        return parsed

    def validate_with_attempts(
        self,
        role: RoleType,
        raw_attempts: list[str],
        max_attempts: int = 2,
    ) -> dict | ValidationFailure:
        attempts = raw_attempts[:max_attempts]
        last_failure: ValidationFailure | None = None
        for raw_text in attempts:
            result = self.validate(role, raw_text)
            if isinstance(result, ValidationFailure):
                last_failure = result
                continue
            return result
        if last_failure is not None:
            return last_failure
        return ValidationFailure(
            code=FailureCode.JSON_PARSE_ERROR,
            message="No validation attempts were provided.",
        )
