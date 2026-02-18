from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=255)


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    job_id: UUID
    resume_id: UUID
    status: str
    failure_reason_code: str | None
    idempotency_key: str | None
    created_at: datetime
    created_by: UUID
