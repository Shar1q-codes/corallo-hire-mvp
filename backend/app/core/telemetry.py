from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
_tenant_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_id", default=None)
_user_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)
_path_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("path", default=None)
_method_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("method", default=None)
_evaluation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("evaluation_id", default=None)


def set_request_context(
    *,
    request_id: str | None = None,
    tenant_id: str | None = None,
    user_id: str | None = None,
    path: str | None = None,
    method: str | None = None,
    evaluation_id: str | None = None,
) -> None:
    if request_id is not None:
        _request_id_ctx.set(request_id)
    if tenant_id is not None:
        _tenant_id_ctx.set(tenant_id)
    if user_id is not None:
        _user_id_ctx.set(user_id)
    if path is not None:
        _path_ctx.set(path)
    if method is not None:
        _method_ctx.set(method)
    if evaluation_id is not None:
        _evaluation_id_ctx.set(evaluation_id)


def clear_request_context() -> None:
    _request_id_ctx.set(None)
    _tenant_id_ctx.set(None)
    _user_id_ctx.set(None)
    _path_ctx.set(None)
    _method_ctx.set(None)
    _evaluation_id_ctx.set(None)


def get_request_context() -> dict[str, str]:
    context: dict[str, str] = {}
    if _request_id_ctx.get():
        context["request_id"] = _request_id_ctx.get() or ""
    if _tenant_id_ctx.get():
        context["tenant_id"] = _tenant_id_ctx.get() or ""
    if _user_id_ctx.get():
        context["user_id"] = _user_id_ctx.get() or ""
    if _path_ctx.get():
        context["path"] = _path_ctx.get() or ""
    if _method_ctx.get():
        context["method"] = _method_ctx.get() or ""
    if _evaluation_id_ctx.get():
        context["evaluation_id"] = _evaluation_id_ctx.get() or ""
    return context


class JSONLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(get_request_context())

        extra = getattr(record, "extra_json", None)
        if isinstance(extra, dict):
            payload.update(extra)

        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
        return json.dumps(payload, ensure_ascii=True)


def configure_json_logging(level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

