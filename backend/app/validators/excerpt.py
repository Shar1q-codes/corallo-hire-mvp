from __future__ import annotations

import random
import re
from collections.abc import Iterator
from typing import Any

from app.validators.failure import ValidationFailure
from app.validators.types import FailureCode

_SENTENCE_SPLIT = re.compile(r"[.!?]+")
_EXCERPT_FAIL_REGEX = re.compile(
    r"\b(hire|reject|shortlist|offer|best|top|rank|score|fit|overall|recommend|should|must hire|do not hire)\b",
    re.IGNORECASE,
)


def _iter_strings(data: Any) -> Iterator[str]:
    if isinstance(data, dict):
        for value in data.values():
            yield from _iter_strings(value)
    elif isinstance(data, list):
        for value in data:
            yield from _iter_strings(value)
    elif isinstance(data, str):
        yield data


def _build_sentences(payload: dict) -> list[str]:
    sentences: list[str] = []
    for text in _iter_strings(payload):
        for chunk in _SENTENCE_SPLIT.split(text):
            sentence = chunk.strip()
            if sentence:
                sentences.append(sentence)
    return sentences


def validate_excerpt_resistance(payload: dict, seed: int = 42) -> ValidationFailure | None:
    sentences = _build_sentences(payload)
    if not sentences:
        return None

    sample_size = min(5, len(sentences))
    rng = random.Random(seed)
    sampled = sentences if len(sentences) <= 5 else rng.sample(sentences, sample_size)

    failed_sentences: list[str] = []
    for sentence in sampled:
        if _EXCERPT_FAIL_REGEX.search(sentence):
            failed_sentences.append(sentence[:120])

    if len(failed_sentences) <= 1:
        return None

    return ValidationFailure(
        code=FailureCode.EXCERPT_RESISTANCE_FAIL,
        message="Sampled excerpts include verdict/ranking/decision language.",
        matches=failed_sentences,
        raw_excerpt=" | ".join(failed_sentences)[:200],
    )

