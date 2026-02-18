from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LLMRequest:
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.1
    max_tokens: int = 1200
    timeout_seconds: float = 30.0


@dataclass(slots=True)
class LLMResponse:
    raw_text: str
    provider_meta: dict[str, Any] | None = None


class ProviderError(Exception):
    def __init__(self, message: str, *, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient

