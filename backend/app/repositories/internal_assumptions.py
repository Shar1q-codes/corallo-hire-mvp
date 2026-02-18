from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.internal_assumption import InternalAssumptionOutput


class InternalAssumptionRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        job_id: UUID,
        resume_id: UUID,
        evaluation_id: UUID,
        created_by: UUID,
        content_json: dict,
        schema_version: int = 1,
    ) -> InternalAssumptionOutput:
        row = InternalAssumptionOutput(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            job_id=job_id,
            resume_id=resume_id,
            evaluation_id=evaluation_id,
            schema_version=schema_version,
            content_json=content_json,
            created_by=created_by,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

