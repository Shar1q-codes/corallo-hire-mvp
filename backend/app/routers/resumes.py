from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import apply_rls_context, get_db_session
from app.core.errors import ApiProblem
from app.core.security import RequestContext, get_request_context
from app.repositories.resumes import ResumeRepository
from app.schemas.resume import ResumeOut, ResumeUploadOut, SignedURLResponse
from app.services.storage import build_resume_object_path, create_signed_download_url, upload_resume_file
from app.utils.ids import new_uuid

router = APIRouter()


@router.post("/workspaces/{workspace_id}/resumes", response_model=ResumeUploadOut, status_code=201)
async def upload_resume(
    workspace_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> ResumeUploadOut:
    await apply_rls_context(session, context)

    resume_id = new_uuid()
    path = build_resume_object_path(
        tenant_id=context.tenant_id,
        workspace_id=workspace_id,
        resume_id=resume_id,
        filename=file.filename or "resume.bin",
    )

    await upload_resume_file(path, file)
    resume = await ResumeRepository.create(
        session,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        workspace_id=workspace_id,
        file_object_path=path,
        original_filename=file.filename,
        mime_type=file.content_type,
        size_bytes=file.size,
    )
    if resume is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Workspace not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return ResumeUploadOut(resume_id=resume.id, file_object_path=resume.file_object_path)


@router.get("/workspaces/{workspace_id}/resumes", response_model=list[ResumeOut])
async def list_resumes(
    workspace_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> list[ResumeOut]:
    await apply_rls_context(session, context)
    resumes = await ResumeRepository.list_by_workspace(session, tenant_id=context.tenant_id, workspace_id=workspace_id)
    return [ResumeOut.model_validate(item) for item in resumes]


@router.get("/resumes/{resume_id}", response_model=ResumeOut)
async def get_resume(
    resume_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> ResumeOut:
    await apply_rls_context(session, context)
    resume = await ResumeRepository.get(session, tenant_id=context.tenant_id, resume_id=resume_id)
    if resume is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Resume not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return ResumeOut.model_validate(resume)


@router.delete("/resumes/{resume_id}", status_code=204)
async def delete_resume(
    resume_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> None:
    await apply_rls_context(session, context)
    deleted = await ResumeRepository.delete(
        session, tenant_id=context.tenant_id, resume_id=resume_id, user_id=context.user_id
    )
    if not deleted:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Resume not found.",
            type_="https://hdis.dev/problems/not-found",
        )


@router.get("/resumes/{resume_id}/download-url", response_model=SignedURLResponse)
async def get_resume_download_url(
    resume_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> SignedURLResponse:
    await apply_rls_context(session, context)
    resume = await ResumeRepository.get(session, tenant_id=context.tenant_id, resume_id=resume_id)
    if resume is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Resume not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    signed_url = await create_signed_download_url(resume.file_object_path, expires_in_seconds=300)
    return SignedURLResponse(url=signed_url, expires_in_seconds=300)

