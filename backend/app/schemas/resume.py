from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    file_object_path: str
    original_filename: str | None
    mime_type: str | None
    size_bytes: int | None
    extracted_text: str | None
    created_at: datetime
    created_by: UUID


class ResumeUploadOut(BaseModel):
    resume_id: UUID
    file_object_path: str


class SignedURLResponse(BaseModel):
    url: str
    expires_in_seconds: int
