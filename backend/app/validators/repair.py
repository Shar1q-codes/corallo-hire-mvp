from app.validators.failure import ValidationFailure
from app.validators.types import FailureCode


def build_repair_instruction(failure: ValidationFailure) -> str:
    if failure.code == FailureCode.JSON_PARSE_ERROR:
        return "Return ONLY valid JSON matching this schema. Do not include prose before or after JSON."
    if failure.code == FailureCode.SCHEMA_INVALID:
        return "Return ONLY valid JSON matching this schema and include all required fields with valid types."
    if failure.code == FailureCode.FORBIDDEN_LANGUAGE:
        matches = ", ".join(failure.matches[:10]) if failure.matches else "forbidden terms"
        return f"Remove forbidden words: {matches}. Keep neutral, non-decision language."
    if failure.code == FailureCode.PROBABILITY_LANGUAGE:
        return "Remove probability/odds/percentage language and keep confidence as Low, Medium, or High only."
    if failure.code == FailureCode.ANTI_COMPRESSION_FAIL:
        return "Remove any summary/overall language and remove summary-like keys or recommendation phrasing."
    if failure.code == FailureCode.RISK_NAMING_INVALID:
        return "Rename risk_statement to 'Mechanism -> Failure Mode' format for every risk."
    if failure.code == FailureCode.EXCERPT_RESISTANCE_FAIL:
        return "Rewrite only to remove verdict/ranking wording so sampled excerpts remain non-decisional."
    return "Return ONLY valid JSON matching this schema."

