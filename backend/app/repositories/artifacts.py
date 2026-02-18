from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact
from app.validators.types import ArtifactType


class ArtifactRepository:
    @staticmethod
    async def list_by_evaluation(session: AsyncSession, *, tenant_id: UUID, evaluation_id: UUID) -> list[Artifact]:
        result = await session.execute(
            select(Artifact)
            .where(Artifact.tenant_id == tenant_id, Artifact.evaluation_id == evaluation_id)
            .order_by(Artifact.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_by_type(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
        artifact_type: str,
    ) -> Artifact | None:
        result = await session.execute(
            select(Artifact)
            .where(
                Artifact.tenant_id == tenant_id,
                Artifact.evaluation_id == evaluation_id,
                Artifact.artifact_type == artifact_type,
            )
            .order_by(Artifact.created_at.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_available_types(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
    ) -> set[str]:
        result = await session.execute(
            select(Artifact.artifact_type).where(
                Artifact.tenant_id == tenant_id,
                Artifact.evaluation_id == evaluation_id,
                Artifact.artifact_type.in_(
                    [
                        ArtifactType.INTENT_HYPOTHESES.value,
                        ArtifactType.RISK_SIGNALS.value,
                        ArtifactType.INTERVIEW_GUIDANCE.value,
                    ]
                ),
            )
        )
        return set(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        job_id: UUID,
        resume_id: UUID,
        evaluation_id: UUID,
        artifact_type: ArtifactType,
        content_json: dict,
        created_by: UUID,
        schema_version: int = 1,
    ) -> Artifact:
        artifact = Artifact(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            job_id=job_id,
            resume_id=resume_id,
            evaluation_id=evaluation_id,
            artifact_type=artifact_type.value,
            schema_version=schema_version,
            content_json=content_json,
            created_by=created_by,
        )
        session.add(artifact)
        await session.commit()
        await session.refresh(artifact)
        return artifact
