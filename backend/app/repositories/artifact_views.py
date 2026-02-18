from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact_views import ArtifactViewEvent


class ArtifactViewRepository:
    @staticmethod
    async def record_view(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        evaluation_id: UUID,
        artifact_type: str,
        detail_json: dict,
    ) -> ArtifactViewEvent:
        row = ArtifactViewEvent(
            tenant_id=tenant_id,
            user_id=user_id,
            evaluation_id=evaluation_id,
            artifact_type=artifact_type,
            detail_json=detail_json,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def get_latest_view_map(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        evaluation_id: UUID,
    ) -> dict[str, datetime]:
        result = await session.execute(
            select(ArtifactViewEvent)
            .where(
                ArtifactViewEvent.tenant_id == tenant_id,
                ArtifactViewEvent.user_id == user_id,
                ArtifactViewEvent.evaluation_id == evaluation_id,
            )
            .order_by(ArtifactViewEvent.viewed_at.desc())
        )
        rows = list(result.scalars().all())
        view_map: dict[str, datetime] = {}
        for row in rows:
            if row.artifact_type not in view_map:
                view_map[row.artifact_type] = row.viewed_at
        return view_map

