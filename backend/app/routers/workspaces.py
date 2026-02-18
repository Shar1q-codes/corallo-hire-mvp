from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import apply_rls_context, get_db_session
from app.core.errors import ApiProblem
from app.core.security import RequestContext, get_request_context
from app.repositories.workspaces import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceOut, WorkspaceUpdate

router = APIRouter()


@router.post("/workspaces", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    payload: WorkspaceCreate,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> WorkspaceOut:
    await apply_rls_context(session, context)
    workspace = await WorkspaceRepository.create(
        session, tenant_id=context.tenant_id, user_id=context.user_id, name=payload.name
    )
    return WorkspaceOut.model_validate(workspace)


@router.get("/workspaces", response_model=list[WorkspaceOut])
async def list_workspaces(
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> list[WorkspaceOut]:
    await apply_rls_context(session, context)
    workspaces = await WorkspaceRepository.list(session, tenant_id=context.tenant_id)
    return [WorkspaceOut.model_validate(item) for item in workspaces]


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(
    workspace_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> WorkspaceOut:
    await apply_rls_context(session, context)
    workspace = await WorkspaceRepository.get(session, tenant_id=context.tenant_id, workspace_id=workspace_id)
    if workspace is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Workspace not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return WorkspaceOut.model_validate(workspace)


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def patch_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> WorkspaceOut:
    await apply_rls_context(session, context)
    workspace = await WorkspaceRepository.update_name(
        session,
        tenant_id=context.tenant_id,
        workspace_id=workspace_id,
        user_id=context.user_id,
        name=payload.name,
    )
    if workspace is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Workspace not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return WorkspaceOut.model_validate(workspace)


@router.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> None:
    await apply_rls_context(session, context)
    deleted = await WorkspaceRepository.delete(
        session, tenant_id=context.tenant_id, workspace_id=workspace_id, user_id=context.user_id
    )
    if not deleted:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Workspace not found.",
            type_="https://hdis.dev/problems/not-found",
        )

