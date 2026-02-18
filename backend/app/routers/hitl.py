from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import apply_rls_context, get_db_session
from app.core.errors import ApiProblem
from app.core.security import RequestContext, get_request_context
from app.repositories.evaluations import EvaluationRepository
from app.repositories.hitl import HITLRepository
from app.schemas.hitl import (
    AckCreate,
    AckRead,
    ArtifactsViewedCreate,
    ChainEventRead,
    DecisionBoundaryCheckRead,
)

router = APIRouter()


@router.post("/evaluations/{evaluation_id}/acknowledgements", status_code=201)
async def create_acknowledgement(
    evaluation_id: UUID,
    payload: AckCreate,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> dict:
    await apply_rls_context(session, context)
    eval_context = await EvaluationRepository.get_context(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if eval_context is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )

    ack = await HITLRepository.insert_acknowledgement(
        session,
        tenant_id=context.tenant_id,
        workspace_id=eval_context.evaluation.workspace_id,
        job_id=eval_context.evaluation.job_id,
        resume_id=eval_context.evaluation.resume_id,
        evaluation_id=evaluation_id,
        acknowledgement_type=payload.acknowledgement_type.value,
        subject_ref_type=payload.subject_ref_type.value,
        subject_ref_id=payload.subject_ref_id,
        content_text=payload.content_text,
        decision_mode=payload.decision_mode.value,
        created_by=context.user_id,
    )

    await HITLRepository.insert_chain_event(
        session,
        tenant_id=context.tenant_id,
        evaluation_id=evaluation_id,
        actor_user_id=context.user_id,
        event_type="acknowledgement_recorded",
        detail_json={
            "acknowledgement_id": str(ack.id),
            "acknowledgement_type": payload.acknowledgement_type.value,
            "decision_mode": payload.decision_mode.value,
        },
    )

    return {"acknowledgement_id": str(ack.id)}


@router.get("/evaluations/{evaluation_id}/acknowledgements", response_model=list[AckRead])
async def list_acknowledgements(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> list[AckRead]:
    await apply_rls_context(session, context)
    eval_row = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if eval_row is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    rows = await HITLRepository.list_acknowledgements_for_evaluation(
        session, tenant_id=context.tenant_id, evaluation_id=evaluation_id
    )
    return [AckRead.model_validate(row) for row in rows]


@router.get("/evaluations/{evaluation_id}/decision-chain", response_model=list[ChainEventRead])
async def list_decision_chain(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> list[ChainEventRead]:
    await apply_rls_context(session, context)
    eval_row = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if eval_row is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    rows = await HITLRepository.list_chain_events_for_evaluation(
        session, tenant_id=context.tenant_id, evaluation_id=evaluation_id
    )
    return [ChainEventRead.model_validate(row) for row in rows]


@router.post("/evaluations/{evaluation_id}/artifacts-viewed", status_code=201)
async def mark_artifacts_viewed(
    evaluation_id: UUID,
    payload: ArtifactsViewedCreate,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> dict:
    await apply_rls_context(session, context)
    eval_row = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if eval_row is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    event = await HITLRepository.insert_chain_event(
        session,
        tenant_id=context.tenant_id,
        evaluation_id=evaluation_id,
        actor_user_id=context.user_id,
        event_type="artifacts_viewed",
        detail_json={"artifact_types": payload.artifact_types},
    )
    return {"event_id": str(event.id)}


@router.post("/evaluations/{evaluation_id}/decision-boundary-check", response_model=DecisionBoundaryCheckRead)
async def decision_boundary_check(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> DecisionBoundaryCheckRead:
    await apply_rls_context(session, context)
    eval_row = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if eval_row is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )

    acks = await HITLRepository.list_acknowledgements_for_evaluation(
        session, tenant_id=context.tenant_id, evaluation_id=evaluation_id
    )
    has_counter_signal_ack = any(
        row.acknowledgement_type == "counter_signal_ack" and len((row.content_text or "").strip()) >= 30 for row in acks
    )
    has_validation_gap = any(
        row.acknowledgement_type == "validation_gap_declaration" and len((row.content_text or "").strip()) >= 30
        for row in acks
    )

    missing: list[str] = []
    if not has_counter_signal_ack:
        missing.append("at least one counter_signal_ack acknowledgement is required")
    if not has_validation_gap:
        missing.append("at least one validation_gap_declaration acknowledgement is required")

    has_risk_artifact = await HITLRepository.has_risk_signals_artifact(
        session, tenant_id=context.tenant_id, evaluation_id=evaluation_id
    )
    if has_risk_artifact:
        has_risk_reference = any(
            row.subject_ref_type == "risk_item" or ((row.subject_ref_id or "").lower().startswith("risk:")) for row in acks
        )
        if not has_risk_reference:
            missing.append("at least one acknowledgement must reference a risk item")

    eligible = len(missing) == 0
    if eligible:
        await HITLRepository.insert_chain_event(
            session,
            tenant_id=context.tenant_id,
            evaluation_id=evaluation_id,
            actor_user_id=context.user_id,
            event_type="final_decision_boundary_reached",
            detail_json={"eligible": True},
        )
    return DecisionBoundaryCheckRead(eligible=eligible, missing=missing)

