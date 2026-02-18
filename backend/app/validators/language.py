from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from app.validators.failure import ValidationFailure
from app.validators.types import FailureCode, RoleType

_FORBIDDEN_PATTERNS = [
    r"\bhire\b",
    r"\bhired\b",
    r"\bhiring decision\b",
    r"\breject\b",
    r"\brejected\b",
    r"\brejection\b",
    r"\bshortlist\b",
    r"\bshortlisted\b",
    r"\badvance\b",
    r"\badvanced\b",
    r"\boffer\b",
    r"\boffered\b",
    r"\bselect\b",
    r"\bselected\b",
    r"\bbest\b",
    r"\btop\b",
    r"\bhighest\b",
    r"\blowest\b",
    r"\brank\b",
    r"\branking\b",
    r"\bscore\b",
    r"\bscoring\b",
    r"\bmatch\b",
    r"\bfit\b",
    r"\bstrong fit\b",
    r"\bgood fit\b",
    r"\bbad fit\b",
    r"\boverall\b",
    r"\bin summary\b",
    r"\bkey takeaway\b",
    r"\bkey takeaways\b",
    r"\bconclusion\b",
    r"\bverdict\b",
    r"\brecommendation\b",
    r"\brecommended\b",
    r"\bclearly\b",
    r"\bdefinitely\b",
    r"\bcertainly\b",
    r"\bguaranteed\b",
    r"\bwill succeed\b",
    r"\bwill fail\b",
    r"\bno doubt\b",
    r"\bhigh-risk candidate\b",
    r"\bsevere\b",
    r"\bdisqualifying\b",
    r"\beliminate\b",
    r"\bred flag candidate\b",
]

_PROBABILITY_PATTERN = re.compile(r"\b\d{1,3}\s?%\b|\bprobability\b|\bodds\b", re.IGNORECASE)

_FORBIDDEN_REGEX = [re.compile(pattern, re.IGNORECASE) for pattern in _FORBIDDEN_PATTERNS]


def _iter_strings(data: Any, path: str = "/") -> Iterator[tuple[str, str]]:
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path.rstrip('/')}/{key}" if path != "/" else f"/{key}"
            yield from _iter_strings(value, child_path)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            child_path = f"{path.rstrip('/')}/{index}" if path != "/" else f"/{index}"
            yield from _iter_strings(value, child_path)
    elif isinstance(data, str):
        yield path, data


def _validate_risk_naming(payload: dict) -> ValidationFailure | None:
    risks = payload.get("risks")
    if not isinstance(risks, list):
        return None
    invalid_paths: list[str] = []
    for idx, risk in enumerate(risks):
        if not isinstance(risk, dict):
            continue
        statement = risk.get("risk_statement")
        if not isinstance(statement, str):
            continue
        separator = "→" if "→" in statement else "->" if "->" in statement else None
        if separator is None:
            invalid_paths.append(f"/risks/{idx}/risk_statement")
            continue
        parts = [part.strip() for part in statement.split(separator)]
        if len(parts) < 2 or not all(parts):
            invalid_paths.append(f"/risks/{idx}/risk_statement")
    if not invalid_paths:
        return None
    return ValidationFailure(
        code=FailureCode.RISK_NAMING_INVALID,
        message="risk_statement must follow 'Mechanism -> Failure Mode' format.",
        paths=invalid_paths,
    )


def validate_language(role: RoleType, payload: dict) -> ValidationFailure | None:
    forbidden_matches: list[str] = []
    forbidden_paths: list[str] = []
    probability_matches: list[str] = []
    probability_paths: list[str] = []
    first_forbidden_excerpt = ""

    for path, text in _iter_strings(payload):
        for pattern in _FORBIDDEN_REGEX:
            match = pattern.search(text)
            if match:
                forbidden_matches.append(match.group(0))
                forbidden_paths.append(path)
                if not first_forbidden_excerpt:
                    first_forbidden_excerpt = text[:200]
        for match in _PROBABILITY_PATTERN.finditer(text):
            probability_matches.append(match.group(0))
            probability_paths.append(path)

    if forbidden_matches:
        return ValidationFailure(
            code=FailureCode.FORBIDDEN_LANGUAGE,
            message="Forbidden language detected.",
            paths=sorted(set(forbidden_paths)),
            matches=sorted(set(forbidden_matches)),
            raw_excerpt=first_forbidden_excerpt,
        )

    if probability_matches:
        return ValidationFailure(
            code=FailureCode.PROBABILITY_LANGUAGE,
            message="Probability or percentage language is not allowed.",
            paths=sorted(set(probability_paths)),
            matches=sorted(set(probability_matches)),
        )

    if role == RoleType.RISK:
        return _validate_risk_naming(payload)

    return None
