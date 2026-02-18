from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.circuit_breaker.breaker import CircuitBreaker
from app.core.config import get_settings
from app.core.db import apply_rls_context, get_db_session
from app.core.errors import ApiProblem, api_problem_from_orchestrator_error
from app.core.security import RequestContext, get_request_context
from app.orchestrator.run import run_evaluation
from app.orchestrator.types import OrchestratorError
from app.rate_limit.in_memory import InMemoryTokenBucket
from app.rate_limit.keys import tenant_run_key

router = APIRouter()
settings = get_settings()

rate_limiter = InMemoryTokenBucket(
    capacity=settings.run_rate_limit_per_minute,
    refill_per_minute=settings.run_rate_limit_per_minute,
)
circuit_breaker = CircuitBreaker(
    error_threshold=settings.breaker_error_threshold,
    window_seconds=settings.breaker_window_seconds,
    cooldown_seconds=settings.breaker_cooldown_seconds,
)


@router.post("/evaluations/{evaluation_id}/run")
async def run_evaluation_endpoint(
    evaluation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    context: RequestContext = Depends(get_request_context),
) -> dict:
    await apply_rls_context(session, context)

    if not rate_limiter.allow(tenant_run_key(context.tenant_id)):
        raise ApiProblem(
            status=429,
            title="Rate limit exceeded",
            detail="Too many evaluation runs for this tenant. Try again later.",
            type_="https://errors.hdis/rate-limit",
        )

    if not circuit_breaker.allow_request():
        raise ApiProblem(
            status=503,
            title="Analysis temporarily unavailable",
            detail="External model provider is unavailable. Try again later.",
            type_="https://errors.hdis/circuit-breaker-open",
        )

    try:
        return await run_evaluation(
            session=session,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            evaluation_id=evaluation_id,
            circuit_breaker=circuit_breaker,
        )
    except OrchestratorError as exc:
        raise api_problem_from_orchestrator_error(exc) from exc

