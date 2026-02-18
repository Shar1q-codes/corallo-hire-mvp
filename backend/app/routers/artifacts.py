from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import apply_rls_context, get_db_session
from app.core.security import RequestContext, get_request_context
from app.repositories.artifacts import ArtifactRepository
from app.schemas.artifact import ArtifactOut

router = APIRouter()


@router.get("/evaluations/{evaluation_id}/artifacts", response_model=list[ArtifactOut])
async def list_artifacts(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> list[ArtifactOut]:
    await apply_rls_context(session, context)
    artifacts = await ArtifactRepository.list_by_evaluation(
        session, tenant_id=context.tenant_id, evaluation_id=evaluation_id
    )
    return [ArtifactOut.model_validate(item) for item in artifacts]

