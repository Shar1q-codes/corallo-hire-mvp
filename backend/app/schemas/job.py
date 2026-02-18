from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=300)
    recruiter_notes: str | None = Field(
        default=None,
        description="Non-authoritative recruiter context; not workflow or outcome state.",
    )


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=300)
    recruiter_notes: str | None = Field(
        default=None,
        description="Non-authoritative recruiter context; not workflow or outcome state.",
    )


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    title: str
    description: str
    recruiter_notes: str | None
    created_at: datetime
    created_by: UUID
