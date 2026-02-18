from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.db import is_rls_denied_error
from app.core.telemetry import get_logger
from app.metrics.registry import metrics_registry
from app.orchestrator.types import OrchestratorError


class ApiProblem(Exception):
    def __init__(
        self,
        status: int,
        title: str,
        detail: str,
        type_: str = "about:blank",
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.status = status
        self.title = title
        self.detail = detail
        self.type = type_
        self.errors = errors or []
        super().__init__(detail)


logger = get_logger(__name__)


def api_problem_from_orchestrator_error(error: OrchestratorError) -> ApiProblem:
    if error.code == "provider_error":
        return ApiProblem(
            status=503,
            title="Analysis temporarily unavailable",
            detail="External model provider is unavailable. Try again later.",
            type_="https://errors.hdis/circuit-breaker-open",
        )
    if error.code == "evaluation_not_found":
        return ApiProblem(
            status=404,
            title="Not Found",
            detail="Evaluation not found.",
            type_="https://hdis.dev/problems/not-found",
        )
    return ApiProblem(
        status=error.http_status,
        title="Orchestrator Error",
        detail=error.message,
        type_="https://errors.hdis/orchestrator",
    )


def _problem_payload(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url.path),
    }
    if errors:
        payload["errors"] = errors
    return payload


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiProblem)
    async def api_problem_handler(request: Request, exc: ApiProblem) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=_problem_payload(
                request,
                status=exc.status,
                title=exc.title,
                detail=exc.detail,
                type_=exc.type,
                errors=exc.errors,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in exc.errors()]
        return JSONResponse(
            status_code=422,
            content=_problem_payload(
                request,
                status=422,
                title="Validation Error",
                detail="Request validation failed.",
                type_="https://hdis.dev/problems/validation-error",
                errors=errors,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if is_rls_denied_error(exc):
            metrics_registry.inc("rls_denied_total")
            logger.warning("RLS denied error detected")
            return JSONResponse(
                status_code=403,
                content=_problem_payload(
                    request,
                    status=403,
                    title="Forbidden",
                    detail="Access denied.",
                    type_="https://hdis.dev/problems/forbidden",
                ),
            )
        return JSONResponse(
            status_code=500,
            content=_problem_payload(
                request,
                status=500,
                title="Internal Server Error",
                detail="An unexpected error occurred.",
                type_="https://hdis.dev/problems/internal-server-error",
            ),
        )
