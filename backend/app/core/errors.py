from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
    async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
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

