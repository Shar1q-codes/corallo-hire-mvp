from __future__ import annotations

from fastapi import APIRouter, Header
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.errors import ApiProblem
from app.metrics.registry import metrics_registry


def _labels_to_str(labels_key: tuple[tuple[str, str], ...]) -> str:
    if not labels_key:
        return ""
    labels = ",".join(f'{k}="{v}"' for k, v in labels_key)
    return f"{{{labels}}}"


def render_metrics_text() -> str:
    snapshot = metrics_registry.snapshot()
    lines: list[str] = []

    for name, series in snapshot["counter"].items():
        for labels_key, value in series.items():
            lines.append(f"{name}{_labels_to_str(labels_key)} {value}")

    for name, series in snapshot["hist_sum"].items():
        count_series = snapshot["hist_count"].get(name, {})
        for labels_key, value in series.items():
            lines.append(f"{name}_sum{_labels_to_str(labels_key)} {value}")
            lines.append(f"{name}_count{_labels_to_str(labels_key)} {count_series.get(labels_key, 0.0)}")

    return "\n".join(lines) + "\n"


def metrics_router() -> APIRouter:
    router = APIRouter()

    @router.get("/metrics", response_class=PlainTextResponse)
    async def get_metrics(x_admin_metrics_secret: str | None = Header(default=None, alias="X-Admin-Metrics-Secret")) -> str:
        settings = get_settings()
        if not settings.metrics_enabled:
            raise ApiProblem(
                status=404,
                title="Not Found",
                detail="Metrics endpoint is disabled.",
                type_="https://hdis.dev/problems/not-found",
            )
        if settings.metrics_admin_secret and x_admin_metrics_secret != settings.metrics_admin_secret:
            raise ApiProblem(
                status=403,
                title="Forbidden",
                detail="Metrics access denied.",
                type_="https://hdis.dev/problems/forbidden",
            )
        return render_metrics_text()

    return router

