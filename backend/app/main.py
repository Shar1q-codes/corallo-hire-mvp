from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.core.telemetry import configure_json_logging
from app.metrics.exporters import metrics_router
from app.metrics.middleware import MetricsMiddleware
from app.middleware.cors import configure_cors
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.tenant_context import TenantContextMiddleware
from app.routers import api_router

settings = get_settings()
configure_json_logging()

app = FastAPI(title=settings.app_name, debug=settings.app_debug)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(TenantContextMiddleware, settings=settings)
app.add_middleware(MetricsMiddleware)
configure_cors(app, settings)

app.include_router(api_router())
app.include_router(metrics_router())
install_error_handlers(app)
