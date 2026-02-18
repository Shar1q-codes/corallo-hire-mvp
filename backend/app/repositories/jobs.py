from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.workspace import Workspace


class JobRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        workspace_id: UUID,
        title: str,
        description: str,
        recruiter_notes: str | None,
    ) -> Job | None:
        workspace_exists = await session.execute(
            select(Workspace.id).where(Workspace.id == workspace_id, Workspace.tenant_id == tenant_id)
        )
        if workspace_exists.scalar_one_or_none() is None:
            return None

        job = Job(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            title=title,
            description=description,
            recruiter_notes=recruiter_notes,
            created_by=user_id,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def list_by_workspace(session: AsyncSession, *, tenant_id: UUID, workspace_id: UUID) -> list[Job]:
        result = await session.execute(
            select(Job)
            .where(Job.tenant_id == tenant_id, Job.workspace_id == workspace_id)
            .order_by(Job.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, *, tenant_id: UUID, job_id: UUID) -> Job | None:
        result = await session.execute(select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        job_id: UUID,
        user_id: UUID,
        title: str | None,
        description: str | None,
        recruiter_notes: str | None,
    ) -> Job | None:
        job = await JobRepository.get(session, tenant_id=tenant_id, job_id=job_id)
        if job is None or job.created_by != user_id:
            return None
        if title is not None:
            job.title = title
        if description is not None:
            job.description = description
        if recruiter_notes is not None:
            job.recruiter_notes = recruiter_notes
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def delete(session: AsyncSession, *, tenant_id: UUID, job_id: UUID, user_id: UUID) -> bool:
        job = await JobRepository.get(session, tenant_id=tenant_id, job_id=job_id)
        if job is None or job.created_by != user_id:
            return False
        await session.delete(job)
        await session.commit()
        return True

