from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import apply_rls_context, get_db_session
from app.core.errors import ApiProblem
from app.core.security import RequestContext, get_request_context
from app.repositories.evaluations import EvaluationRepository
from app.schemas.evaluation import EvaluationCreate, EvaluationOut

router = APIRouter()


@router.post("/jobs/{job_id}/resumes/{resume_id}/evaluations", response_model=EvaluationOut, status_code=201)
async def create_evaluation(
    job_id: UUID,
    resume_id: UUID,
    payload: EvaluationCreate,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> EvaluationOut:
    await apply_rls_context(session, context)
    evaluation = await EvaluationRepository.create(
        session,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        job_id=job_id,
        resume_id=resume_id,
        idempotency_key=payload.idempotency_key,
    )
    if evaluation is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Job or resume not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return EvaluationOut.model_validate(evaluation)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationOut)
async def get_evaluation(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> EvaluationOut:
    await apply_rls_context(session, context)
    evaluation = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if evaluation is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return EvaluationOut.model_validate(evaluation)

