from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import apply_rls_context, get_db_session
from app.core.errors import ApiProblem
from app.core.security import RequestContext, get_request_context
from app.repositories.artifact_views import ArtifactViewRepository
from app.repositories.artifacts import ArtifactRepository
from app.repositories.audit import AuditRepository
from app.repositories.evaluations import EvaluationRepository
from app.repositories.hitl import HITLRepository
from app.services.artifact_gates import gate_reason
from app.validators.types import ArtifactType

router = APIRouter()
_ALLOWED_TYPES = {
    ArtifactType.INTENT_HYPOTHESES.value,
    ArtifactType.RISK_SIGNALS.value,
    ArtifactType.INTERVIEW_GUIDANCE.value,
}


def _validate_artifact_type(artifact_type: str) -> str:
    if artifact_type not in _ALLOWED_TYPES:
        raise ApiProblem(
            status=422,
            title="Validation Error",
            detail="artifact_type must be one of intent_hypotheses, risk_signals, interview_guidance.",
            type_="https://hdis.dev/problems/validation-error",
        )
    return artifact_type


@router.post("/evaluations/{evaluation_id}/artifacts/{artifact_type}/viewed", status_code=201)
async def record_artifact_view(
    evaluation_id: UUID,
    artifact_type: str,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> dict:
    await apply_rls_context(session, context)
    artifact_type = _validate_artifact_type(artifact_type)

    evaluation = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if evaluation is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )

    event = await ArtifactViewRepository.record_view(
        session,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        evaluation_id=evaluation_id,
        artifact_type=artifact_type,
        detail_json={},
    )

    await HITLRepository.insert_chain_event(
        session,
        tenant_id=context.tenant_id,
        evaluation_id=evaluation_id,
        actor_user_id=context.user_id,
        event_type="artifacts_viewed",
        detail_json={"artifact_types": [artifact_type]},
    )

    return {"ok": True, "artifact_type": artifact_type, "viewed_at": event.viewed_at}


@router.get("/evaluations/{evaluation_id}/artifacts/status")
async def artifacts_status(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> dict:
    await apply_rls_context(session, context)
    evaluation = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if evaluation is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )

    available_types = await ArtifactRepository.get_available_types(
        session, tenant_id=context.tenant_id, evaluation_id=evaluation_id
    )
    viewed_map = await ArtifactViewRepository.get_latest_view_map(
        session,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        evaluation_id=evaluation_id,
    )

    intent = ArtifactType.INTENT_HYPOTHESES.value
    risk = ArtifactType.RISK_SIGNALS.value
    interview = ArtifactType.INTERVIEW_GUIDANCE.value

    return {
        "available": {
            intent: intent in available_types,
            risk: risk in available_types,
            interview: interview in available_types,
        },
        "viewed": {
            intent: viewed_map.get(intent),
            risk: viewed_map.get(risk),
            interview: viewed_map.get(interview),
        },
        "gates": {
            "risk_signals_unlocked": gate_reason(artifact_type=risk, viewed=viewed_map) is None,
            "interview_guidance_unlocked": gate_reason(artifact_type=interview, viewed=viewed_map) is None,
        },
    }


@router.get("/evaluations/{evaluation_id}/artifacts/{artifact_type}")
async def get_artifact_by_type(
    evaluation_id: UUID,
    artifact_type: str,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> dict:
    await apply_rls_context(session, context)
    artifact_type = _validate_artifact_type(artifact_type)

    evaluation = await EvaluationRepository.get(session, tenant_id=context.tenant_id, evaluation_id=evaluation_id)
    if evaluation is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )

    viewed_map = await ArtifactViewRepository.get_latest_view_map(
        session,
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        evaluation_id=evaluation_id,
    )
    reason = gate_reason(artifact_type=artifact_type, viewed=viewed_map)
    if reason is not None:
        await AuditRepository.create(
            session,
            tenant_id=context.tenant_id,
            actor_user_id=context.user_id,
            entity_type="artifact",
            entity_id=None,
            action="artifact_gate_blocked",
            detail_json={
                "evaluation_id": str(evaluation_id),
                "artifact_type": artifact_type,
                "gate_reason": reason,
            },
        )
        raise ApiProblem(
            status=403,
            title="Artifact access is gated",
            detail=reason,
            type_="https://errors.hdis/artifact-gate",
        )

    artifact = await ArtifactRepository.get_latest_by_type(
        session,
        tenant_id=context.tenant_id,
        evaluation_id=evaluation_id,
        artifact_type=artifact_type,
    )
    if artifact is None:
        raise ApiProblem(
            status=404,
            title="Not Found",
            detail="Artifact not found.",
            type_="https://hdis.dev/problems/not-found",
        )

    await AuditRepository.create(
        session,
        tenant_id=context.tenant_id,
        actor_user_id=context.user_id,
        entity_type="artifact",
        entity_id=artifact.id,
        action="artifact_read",
        detail_json={"evaluation_id": str(evaluation_id), "artifact_type": artifact_type},
    )
    return {
        "artifact_type": artifact_type,
        "evaluation_id": str(evaluation_id),
        "content_json": artifact.content_json,
        "created_at": artifact.created_at,
    }
