from pathlib import Path
import sys
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.circuit_breaker.breaker import BreakerState, CircuitBreaker  # noqa: E402
from app.core.db import get_db_session  # noqa: E402
from app.main import app  # noqa: E402
from app.rate_limit.in_memory import InMemoryTokenBucket  # noqa: E402


def _token(user_id: str, tenant_id: str | None) -> str:
    payload = {"sub": user_id}
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    return jwt.encode(payload, "test-secret", algorithm="HS256")


async def _fake_session():
    yield object()


def test_run_endpoint_fails_closed_without_tenant_claim() -> None:
    client = TestClient(app)
    bearer = _token(str(uuid4()), None)
    response = client.post(f"/evaluations/{uuid4()}/run", headers={"Authorization": f"Bearer {bearer}"})
    assert response.status_code == 401


def test_run_endpoint_rate_limit_returns_429(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    eval_id = uuid4()

    async def _run(*_args, **_kwargs):
        return {"evaluation_id": str(eval_id), "status": "completed", "failure_reason_code": None}

    async def _noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.routers.evaluations_run.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.evaluations_run.run_evaluation", _run)
    monkeypatch.setattr("app.routers.evaluations_run.rate_limiter", InMemoryTokenBucket(capacity=1, refill_per_minute=1))
    monkeypatch.setattr(
        "app.routers.evaluations_run.circuit_breaker",
        CircuitBreaker(error_threshold=5, window_seconds=60, cooldown_seconds=120),
    )
    app.dependency_overrides[get_db_session] = _fake_session

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}

    first = client.post(f"/evaluations/{eval_id}/run", headers=headers)
    second = client.post(f"/evaluations/{eval_id}/run", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["type"] == "https://errors.hdis/rate-limit"
    app.dependency_overrides.clear()


def test_run_endpoint_breaker_open_returns_503(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    eval_id = uuid4()

    async def _noop(*_args, **_kwargs):
        return None

    breaker = CircuitBreaker(error_threshold=1, window_seconds=60, cooldown_seconds=120)
    breaker._state = BreakerState.OPEN
    breaker._opened_at = 9999999999.0

    monkeypatch.setattr("app.routers.evaluations_run.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.evaluations_run.rate_limiter", InMemoryTokenBucket(capacity=10, refill_per_minute=10))
    monkeypatch.setattr("app.routers.evaluations_run.circuit_breaker", breaker)
    app.dependency_overrides[get_db_session] = _fake_session

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}
    response = client.post(f"/evaluations/{eval_id}/run", headers=headers)

    assert response.status_code == 503
    assert response.json()["type"] == "https://errors.hdis/circuit-breaker-open"
    app.dependency_overrides.clear()
