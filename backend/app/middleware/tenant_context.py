from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import Settings
from app.core.errors import ApiProblem
from app.core.security import build_request_context


class TenantContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        try:
            context = build_request_context(request.headers.get("authorization"), self.settings)
        except ApiProblem:
            raise

        request.state.request_context = context
        request.state.tenant_id = str(context.tenant_id)
        request.state.user_id = str(context.user_id)
        return await call_next(request)

