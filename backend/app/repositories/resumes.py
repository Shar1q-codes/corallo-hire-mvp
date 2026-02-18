from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.workspace import Workspace


class ResumeRepository:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        user_id: UUID,
        workspace_id: UUID,
        file_object_path: str,
        original_filename: str | None,
        mime_type: str | None,
        size_bytes: int | None,
    ) -> Resume | None:
        workspace_exists = await session.execute(
            select(Workspace.id).where(Workspace.id == workspace_id, Workspace.tenant_id == tenant_id)
        )
        if workspace_exists.scalar_one_or_none() is None:
            return None

        resume = Resume(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            file_object_path=file_object_path,
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            extracted_text=None,
            created_by=user_id,
        )
        session.add(resume)
        await session.commit()
        await session.refresh(resume)
        return resume

    @staticmethod
    async def list_by_workspace(session: AsyncSession, *, tenant_id: UUID, workspace_id: UUID) -> list[Resume]:
        result = await session.execute(
            select(Resume)
            .where(Resume.tenant_id == tenant_id, Resume.workspace_id == workspace_id)
            .order_by(Resume.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, *, tenant_id: UUID, resume_id: UUID) -> Resume | None:
        result = await session.execute(select(Resume).where(Resume.id == resume_id, Resume.tenant_id == tenant_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(session: AsyncSession, *, tenant_id: UUID, resume_id: UUID, user_id: UUID) -> bool:
        resume = await ResumeRepository.get(session, tenant_id=tenant_id, resume_id=resume_id)
        if resume is None or resume.created_by != user_id:
            return False
        await session.delete(resume)
        await session.commit()
        return True

