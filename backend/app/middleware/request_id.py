import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.telemetry import clear_request_context, set_request_context


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        clear_request_context()
        request_id = request.headers.get("x-request-id") or request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_context(request_id=request_id, path=request.url.path, method=request.method)
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["X-Request-Id"] = request_id
        return response
