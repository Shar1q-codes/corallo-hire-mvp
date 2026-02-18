from pathlib import Path
import sys
from uuid import uuid4

import jwt
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.core.errors import ApiProblem  # noqa: E402
from app.core.security import build_request_context  # noqa: E402


def _bearer(payload: dict) -> str:
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return f"Bearer {token}"


def test_jwt_parses_user_and_tenant_claims() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    user_id = uuid4()
    tenant_id = uuid4()

    context = build_request_context(
        _bearer({"sub": str(user_id), "tenant_id": str(tenant_id)}),
        settings,
    )
    assert str(context.user_id) == str(user_id)
    assert str(context.tenant_id) == str(tenant_id)


def test_jwt_missing_tenant_claim_fails_closed() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    with pytest.raises(ApiProblem) as exc:
        build_request_context(_bearer({"sub": str(uuid4())}), settings)
    assert exc.value.status == 401


def test_jwt_invalid_tenant_uuid_fails_closed() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    with pytest.raises(ApiProblem) as exc:
        build_request_context(_bearer({"sub": str(uuid4()), "tenant_id": "not-a-uuid"}), settings)
    assert exc.value.status == 401

