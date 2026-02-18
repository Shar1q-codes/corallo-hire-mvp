from dataclasses import dataclass, field

from app.validators.types import FailureCode


@dataclass(slots=True)
class ValidationFailure:
    code: FailureCode
    message: str
    paths: list[str] = field(default_factory=list)
    matches: list[str] = field(default_factory=list)
    raw_excerpt: str = ""

    def __post_init__(self) -> None:
        if len(self.raw_excerpt) > 200:
            self.raw_excerpt = self.raw_excerpt[:200]

