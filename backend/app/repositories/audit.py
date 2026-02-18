from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        actor_user_id: UUID,
        entity_type: str,
        entity_id: UUID | None,
        action: str,
        detail_json: dict,
    ) -> AuditLog:
        record = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            detail_json=detail_json,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def log_stage(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        actor_user_id: UUID,
        evaluation_id: UUID,
        role: str,
        action: str,
        detail_json: dict,
    ) -> AuditLog:
        return await AuditRepository.create(
            session,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            entity_type="evaluation",
            entity_id=evaluation_id,
            action=action,
            detail_json={"role": role, **detail_json},
        )
