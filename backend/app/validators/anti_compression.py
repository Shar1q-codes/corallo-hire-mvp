from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.validators.failure import ValidationFailure
from app.validators.types import FailureCode

_FORBIDDEN_PHRASES = [
    "overall",
    "in summary",
    "key takeaways",
    "final recommendation",
    "overall assessment",
]

_FORBIDDEN_KEYS = {"summary", "overall", "takeaway", "recommendation"}


def _iter_nodes(data: Any, path: str = "/") -> Iterator[tuple[str, Any]]:
    yield path, data
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path.rstrip('/')}/{key}" if path != "/" else f"/{key}"
            yield from _iter_nodes(value, child_path)
    elif isinstance(data, list):
        for index, value in enumerate(data):
            child_path = f"{path.rstrip('/')}/{index}" if path != "/" else f"/{index}"
            yield from _iter_nodes(value, child_path)


def validate_anti_compression(payload: dict) -> ValidationFailure | None:
    matches: list[str] = []
    paths: list[str] = []

    for path, node in _iter_nodes(payload):
        if isinstance(node, dict):
            for key in node.keys():
                if key.lower() in _FORBIDDEN_KEYS:
                    matches.append(key)
                    paths.append(path)
        elif isinstance(node, str):
            lowered = node.lower()
            for phrase in _FORBIDDEN_PHRASES:
                if phrase in lowered:
                    matches.append(phrase)
                    paths.append(path)

    if not matches:
        return None

    return ValidationFailure(
        code=FailureCode.ANTI_COMPRESSION_FAIL,
        message="Compression or summary language is not allowed.",
        paths=sorted(set(paths)),
        matches=sorted(set(matches)),
    )

