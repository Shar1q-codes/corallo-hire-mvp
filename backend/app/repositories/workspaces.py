from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace


class WorkspaceRepository:
    @staticmethod
    async def create(session: AsyncSession, *, tenant_id: UUID, user_id: UUID, name: str) -> Workspace:
        workspace = Workspace(tenant_id=tenant_id, created_by=user_id, name=name)
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)
        return workspace

    @staticmethod
    async def list(session: AsyncSession, *, tenant_id: UUID) -> list[Workspace]:
        result = await session.execute(
            select(Workspace).where(Workspace.tenant_id == tenant_id).order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, *, tenant_id: UUID, workspace_id: UUID) -> Workspace | None:
        result = await session.execute(
            select(Workspace).where(Workspace.id == workspace_id, Workspace.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_name(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        workspace_id: UUID,
        user_id: UUID,
        name: str,
    ) -> Workspace | None:
        workspace = await WorkspaceRepository.get(session, tenant_id=tenant_id, workspace_id=workspace_id)
        if workspace is None or workspace.created_by != user_id:
            return None
        workspace.name = name
        await session.commit()
        await session.refresh(workspace)
        return workspace

    @staticmethod
    async def delete(session: AsyncSession, *, tenant_id: UUID, workspace_id: UUID, user_id: UUID) -> bool:
        workspace = await WorkspaceRepository.get(session, tenant_id=tenant_id, workspace_id=workspace_id)
        if workspace is None or workspace.created_by != user_id:
            return False
        await session.delete(workspace)
        await session.commit()
        return True

