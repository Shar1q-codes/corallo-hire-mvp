from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import apply_rls_context, get_db_session
from app.core.errors import ApiProblem
from app.core.security import RequestContext, get_request_context
from app.repositories.jobs import JobRepository
from app.schemas.job import JobCreate, JobOut, JobUpdate

router = APIRouter()


@router.post("/workspaces/{workspace_id}/jobs", response_model=JobOut, status_code=201)
async def create_job(
    workspace_id: UUID,
    payload: JobCreate,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> JobOut:
    await apply_rls_context(session, context)
    job = await JobRepository.create(
        session,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        workspace_id=workspace_id,
        title=payload.title,
        description=payload.description,
        recruiter_notes=payload.recruiter_notes,
    )
    if job is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Workspace not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return JobOut.model_validate(job)


@router.get("/workspaces/{workspace_id}/jobs", response_model=list[JobOut])
async def list_jobs(
    workspace_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> list[JobOut]:
    await apply_rls_context(session, context)
    jobs = await JobRepository.list_by_workspace(session, tenant_id=context.tenant_id, workspace_id=workspace_id)
    return [JobOut.model_validate(item) for item in jobs]


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> JobOut:
    await apply_rls_context(session, context)
    job = await JobRepository.get(session, tenant_id=context.tenant_id, job_id=job_id)
    if job is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Job not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return JobOut.model_validate(job)


@router.patch("/jobs/{job_id}", response_model=JobOut)
async def patch_job(
    job_id: UUID,
    payload: JobUpdate,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> JobOut:
    await apply_rls_context(session, context)
    job = await JobRepository.update(
        session,
        tenant_id=context.tenant_id,
        job_id=job_id,
        user_id=context.user_id,
        title=payload.title,
        description=payload.description,
        recruiter_notes=payload.recruiter_notes,
    )
    if job is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Job not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return JobOut.model_validate(job)


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> None:
    await apply_rls_context(session, context)
    deleted = await JobRepository.delete(session, tenant_id=context.tenant_id, job_id=job_id, user_id=context.user_id)
    if not deleted:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Job not found.",
            type_="https://hdis.dev/problems/not-found",
        )

