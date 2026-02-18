from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact


class ArtifactRepository:
    @staticmethod
    async def list_by_evaluation(session: AsyncSession, *, tenant_id: UUID, evaluation_id: UUID) -> list[Artifact]:
        result = await session.execute(
            select(Artifact)
            .where(Artifact.tenant_id == tenant_id, Artifact.evaluation_id == evaluation_id)
            .order_by(Artifact.created_at.asc())
        )
        return list(result.scalars().all())

