from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    actor_user_id: UUID
    entity_type: str
    entity_id: UUID | None
    action: str
    detail_json: dict
    created_at: datetime
