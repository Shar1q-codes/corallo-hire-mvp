from __future__ import annotations

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.metrics.registry import metrics_registry


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        latency = time.perf_counter() - start
        path = request.url.path
        metrics_registry.observe("request_latency_seconds", latency, labels={"path": path})
        metrics_registry.inc("http_requests_total", labels={"path": path, "status": str(response.status_code)})
        return response

