from __future__ import annotations

import json
from pathlib import Path
import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.circuit_breaker.breaker import CircuitBreaker
from app.core.telemetry import get_logger, set_request_context
from app.llm.client import LLMClient, get_llm_client
from app.llm.models import ProviderError
from app.metrics.registry import metrics_registry
from app.orchestrator.types import OrchestratorError, RoleRunResult
from app.repositories.artifacts import ArtifactRepository
from app.repositories.audit import AuditRepository
from app.repositories.evaluations import EvaluationContext, EvaluationRepository
from app.repositories.internal_assumptions import InternalAssumptionRepository
from app.validators.bundle import ValidationPipeline
from app.validators.failure import ValidationFailure
from app.validators.repair import build_repair_instruction
from app.validators.types import ArtifactType, RoleType

_ROLE_ORDER: list[RoleType] = [RoleType.INTENT, RoleType.RISK, RoleType.ASSUMPTION, RoleType.INTERVIEW]
_PROMPT_FILES: dict[RoleType, str] = {
    RoleType.INTENT: "intent_system.txt",
    RoleType.RISK: "risk_system.txt",
    RoleType.ASSUMPTION: "assumption_system.txt",
    RoleType.INTERVIEW: "interview_system.txt",
}
logger = get_logger(__name__)


def _prompt_text(role: RoleType) -> str:
    path = Path(__file__).resolve().parent / "prompts" / _PROMPT_FILES[role]
    return path.read_text(encoding="utf-8")


def _base_user_payload(context: EvaluationContext) -> dict:
    return {
        "job_description": context.job.description,
        "recruiter_notes": context.job.recruiter_notes or "",
        "resume_text": context.resume.extracted_text or "text unavailable",
    }


def _upstream_payload(
    role: RoleType,
    *,
    intent_output: dict | None,
    risk_output: dict | None,
    assumption_output: dict | None,
) -> dict:
    payload: dict[str, dict] = {}
    if role in (RoleType.RISK, RoleType.ASSUMPTION, RoleType.INTERVIEW) and intent_output is not None:
        payload["intent_output"] = intent_output
    if role in (RoleType.ASSUMPTION, RoleType.INTERVIEW) and risk_output is not None:
        payload["risk_output"] = risk_output
    if role == RoleType.INTERVIEW and assumption_output is not None:
        payload["assumption_output"] = assumption_output
    return payload


def _messages_for_role(
    role: RoleType,
    context: EvaluationContext,
    *,
    intent_output: dict | None,
    risk_output: dict | None,
    assumption_output: dict | None,
    repair_instruction: str | None = None,
) -> list[dict[str, str]]:
    payload = _base_user_payload(context)
    payload.update(
        _upstream_payload(
            role,
            intent_output=intent_output,
            risk_output=risk_output,
            assumption_output=assumption_output,
        )
    )
    user_content = json.dumps(payload, ensure_ascii=True)
    if repair_instruction:
        user_content = f"{user_content}\n\nRepair instruction:\n{repair_instruction}"
    return [
        {"role": "system", "content": _prompt_text(role)},
        {"role": "user", "content": user_content},
    ]


async def _persist_role_output(
    *,
    session: AsyncSession,
    context: EvaluationContext,
    user_id: UUID,
    role: RoleType,
    payload: dict,
) -> None:
    if role == RoleType.INTENT:
        await ArtifactRepository.create(
            session,
            tenant_id=context.evaluation.tenant_id,
            workspace_id=context.evaluation.workspace_id,
            job_id=context.evaluation.job_id,
            resume_id=context.evaluation.resume_id,
            evaluation_id=context.evaluation.id,
            artifact_type=ArtifactType.INTENT_HYPOTHESES,
            content_json=payload,
            created_by=user_id,
        )
        return
    if role == RoleType.RISK:
        await ArtifactRepository.create(
            session,
            tenant_id=context.evaluation.tenant_id,
            workspace_id=context.evaluation.workspace_id,
            job_id=context.evaluation.job_id,
            resume_id=context.evaluation.resume_id,
            evaluation_id=context.evaluation.id,
            artifact_type=ArtifactType.RISK_SIGNALS,
            content_json=payload,
            created_by=user_id,
        )
        return
    if role == RoleType.ASSUMPTION:
        await InternalAssumptionRepository.create(
            session,
            tenant_id=context.evaluation.tenant_id,
            workspace_id=context.evaluation.workspace_id,
            job_id=context.evaluation.job_id,
            resume_id=context.evaluation.resume_id,
            evaluation_id=context.evaluation.id,
            content_json=payload,
            created_by=user_id,
        )
        return
    await ArtifactRepository.create(
        session,
        tenant_id=context.evaluation.tenant_id,
        workspace_id=context.evaluation.workspace_id,
        job_id=context.evaluation.job_id,
        resume_id=context.evaluation.resume_id,
        evaluation_id=context.evaluation.id,
        artifact_type=ArtifactType.INTERVIEW_GUIDANCE,
        content_json=payload,
        created_by=user_id,
    )


async def run_evaluation(
    *,
    session: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    evaluation_id: UUID,
    llm_client: LLMClient | None = None,
    validation_pipeline: ValidationPipeline | None = None,
    circuit_breaker: CircuitBreaker | None = None,
) -> dict:
    evaluation_start = time.perf_counter()
    llm = llm_client or get_llm_client()
    pipeline = validation_pipeline or ValidationPipeline()
    set_request_context(evaluation_id=str(evaluation_id))

    context = await EvaluationRepository.get_context(session, tenant_id=tenant_id, evaluation_id=evaluation_id)
    if context is None:
        raise OrchestratorError("evaluation_not_found", "Evaluation not found.", http_status=404)

    evaluation = context.evaluation
    if evaluation.status == "completed":
        if circuit_breaker is not None:
            circuit_breaker.record_success()
        return {"evaluation_id": str(evaluation.id), "status": "completed", "failure_reason_code": None}
    if evaluation.status == "failed":
        if circuit_breaker is not None:
            circuit_breaker.record_success()
        return {
            "evaluation_id": str(evaluation.id),
            "status": "failed",
            "failure_reason_code": evaluation.failure_reason_code,
        }

    intent_output: dict | None = None
    risk_output: dict | None = None
    assumption_output: dict | None = None
    metrics_registry.inc("evaluations_started_total")

    for role in _ROLE_ORDER:
        role_result: RoleRunResult | None = None
        role_start = time.perf_counter()
        for attempt in (1, 2):
            metrics_registry.inc("role_attempts_total", labels={"role": role.value, "attempt": str(attempt)})
            repair_instruction: str | None = None
            if role_result and role_result.failure:
                repair_instruction = build_repair_instruction(role_result.failure)

            try:
                raw_text = llm.generate(
                    role,
                    _messages_for_role(
                        role,
                        context,
                        intent_output=intent_output,
                        risk_output=risk_output,
                        assumption_output=assumption_output,
                        repair_instruction=repair_instruction,
                    ),
                    temperature=0.1,
                    max_tokens=1200,
                )
            except ProviderError as exc:
                if circuit_breaker is not None:
                    circuit_breaker.record_provider_error()
                metrics_registry.inc("provider_errors_total")
                logger.error("Provider error during role run", extra={"extra_json": {"role": role.value}})
                raise OrchestratorError("provider_error", str(exc), http_status=503) from exc

            validation = pipeline.validate(role, raw_text)
            if isinstance(validation, ValidationFailure):
                metrics_registry.inc(
                    "validator_failures_total",
                    labels={"role": role.value, "code": validation.code.value},
                )
                logger.warning(
                    "Validator failure",
                    extra={
                        "extra_json": {
                            "role": role.value,
                            "failure_code": validation.code.value,
                            "paths": validation.paths,
                            "matches": validation.matches,
                            "raw_excerpt": validation.raw_excerpt[:200],
                        }
                    },
                )
                role_result = RoleRunResult(role=role, attempts=attempt, payload=None, failure=validation)
                if attempt == 2:
                    await EvaluationRepository.mark_failed(
                        session,
                        tenant_id=tenant_id,
                        evaluation_id=evaluation_id,
                        failure_reason_code=validation.code.value,
                    )
                    await AuditRepository.log_stage(
                        session,
                        tenant_id=tenant_id,
                        actor_user_id=user_id,
                        evaluation_id=evaluation_id,
                        role=role.value,
                        action="evaluation_failed",
                        detail_json={"failure_code": validation.code.value, "attempts": 2},
                    )
                    if circuit_breaker is not None:
                        circuit_breaker.record_success()
                    metrics_registry.observe("role_latency_seconds", time.perf_counter() - role_start, labels={"role": role.value})
                    metrics_registry.inc("evaluations_failed_total")
                    metrics_registry.observe("evaluation_total_latency_seconds", time.perf_counter() - evaluation_start)
                    return {
                        "evaluation_id": str(evaluation_id),
                        "status": "failed",
                        "failure_reason_code": validation.code.value,
                    }
                continue

            role_result = RoleRunResult(role=role, attempts=attempt, payload=validation, failure=None)
            await _persist_role_output(
                session=session,
                context=context,
                user_id=user_id,
                role=role,
                payload=validation,
            )
            await AuditRepository.log_stage(
                session,
                tenant_id=tenant_id,
                actor_user_id=user_id,
                evaluation_id=evaluation_id,
                role=role.value,
                action="role_completed",
                detail_json={"attempts": attempt},
            )
            if role == RoleType.INTENT:
                intent_output = validation
            elif role == RoleType.RISK:
                risk_output = validation
            elif role == RoleType.ASSUMPTION:
                assumption_output = validation
            metrics_registry.observe("role_latency_seconds", time.perf_counter() - role_start, labels={"role": role.value})
            break

    await EvaluationRepository.mark_completed(session, tenant_id=tenant_id, evaluation_id=evaluation_id)
    await AuditRepository.log_stage(
        session,
        tenant_id=tenant_id,
        actor_user_id=user_id,
        evaluation_id=evaluation_id,
        role="pipeline",
        action="evaluation_completed",
        detail_json={},
    )
    if circuit_breaker is not None:
        circuit_breaker.record_success()
    metrics_registry.inc("evaluations_completed_total")
    metrics_registry.observe("evaluation_total_latency_seconds", time.perf_counter() - evaluation_start)
    return {"evaluation_id": str(evaluation_id), "status": "completed", "failure_reason_code": None}
