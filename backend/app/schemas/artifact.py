from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    job_id: UUID
    resume_id: UUID
    evaluation_id: UUID
    artifact_type: str
    schema_version: int
    content_json: dict
    created_at: datetime
    created_by: UUID
