from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.job import Job
from app.models.resume import Resume


class EvaluationRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        job_id: UUID,
        resume_id: UUID,
        idempotency_key: str | None,
    ) -> Evaluation | None:
        job_result = await session.execute(select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id))
        job = job_result.scalar_one_or_none()
        if job is None:
            return None

        resume_result = await session.execute(select(Resume).where(Resume.id == resume_id, Resume.tenant_id == tenant_id))
        resume = resume_result.scalar_one_or_none()
        if resume is None:
            return None

        if job.workspace_id != resume.workspace_id:
            return None

        evaluation = Evaluation(
            tenant_id=tenant_id,
            workspace_id=job.workspace_id,
            job_id=job_id,
            resume_id=resume_id,
            status="created",
            failure_reason_code=None,
            idempotency_key=idempotency_key,
            created_by=user_id,
        )
        session.add(evaluation)
        await session.commit()
        await session.refresh(evaluation)
        return evaluation

    @staticmethod
    async def get(session: AsyncSession, *, tenant_id: UUID, evaluation_id: UUID) -> Evaluation | None:
        result = await session.execute(
            select(Evaluation).where(Evaluation.id == evaluation_id, Evaluation.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

