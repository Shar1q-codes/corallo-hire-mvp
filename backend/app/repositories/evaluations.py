from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import Evaluation
from app.models.job import Job
from app.models.resume import Resume


@dataclass(slots=True)
class EvaluationContext:
    evaluation: Evaluation
    job: Job
    resume: Resume


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
        if idempotency_key:
            existing_result = await session.execute(
                select(Evaluation).where(
                    Evaluation.tenant_id == tenant_id,
                    Evaluation.idempotency_key == idempotency_key,
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing is not None:
                return existing

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

    @staticmethod
    async def get_context(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
    ) -> EvaluationContext | None:
        evaluation = await EvaluationRepository.get(session, tenant_id=tenant_id, evaluation_id=evaluation_id)
        if evaluation is None:
            return None

        job_result = await session.execute(
            select(Job).where(Job.id == evaluation.job_id, Job.tenant_id == tenant_id, Job.workspace_id == evaluation.workspace_id)
        )
        job = job_result.scalar_one_or_none()
        if job is None:
            return None

        resume_result = await session.execute(
            select(Resume).where(
                Resume.id == evaluation.resume_id, Resume.tenant_id == tenant_id, Resume.workspace_id == evaluation.workspace_id
            )
        )
        resume = resume_result.scalar_one_or_none()
        if resume is None:
            return None

        return EvaluationContext(evaluation=evaluation, job=job, resume=resume)

    @staticmethod
    async def mark_completed(session: AsyncSession, *, tenant_id: UUID, evaluation_id: UUID) -> Evaluation | None:
        evaluation = await EvaluationRepository.get(session, tenant_id=tenant_id, evaluation_id=evaluation_id)
        if evaluation is None:
            return None
        evaluation.status = "completed"
        evaluation.failure_reason_code = None
        await session.commit()
        await session.refresh(evaluation)
        return evaluation

    @staticmethod
    async def mark_failed(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        evaluation_id: UUID,
        failure_reason_code: str,
    ) -> Evaluation | None:
        evaluation = await EvaluationRepository.get(session, tenant_id=tenant_id, evaluation_id=evaluation_id)
        if evaluation is None:
            return None
        evaluation.status = "failed"
        evaluation.failure_reason_code = failure_reason_code
        await session.commit()
        await session.refresh(evaluation)
        return evaluation
