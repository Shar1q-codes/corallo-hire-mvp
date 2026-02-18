from dataclasses import dataclass

from app.validators.failure import ValidationFailure
from app.validators.types import RoleType


@dataclass(slots=True)
class RoleRunResult:
    role: RoleType
    attempts: int
    payload: dict | None
    failure: ValidationFailure | None


class OrchestratorError(Exception):
    def __init__(self, code: str, message: str, *, http_status: int = 500) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status

