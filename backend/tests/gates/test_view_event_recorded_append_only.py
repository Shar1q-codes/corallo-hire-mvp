from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.core.db import get_db_session  # noqa: E402
from app.main import app  # noqa: E402


def _token(user_id: str, tenant_id: str) -> str:
    return jwt.encode({"sub": user_id, "tenant_id": tenant_id}, "test-secret", algorithm="HS256")


async def _fake_session():
    yield object()


def test_view_event_recorded_endpoint(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    evaluation_id = uuid4()
    recorded = {"view": False, "chain": False}

    async def _noop(*_args, **_kwargs):
        return None

    async def _eval(*_args, **_kwargs):
        return SimpleNamespace(id=evaluation_id)

    async def _record(*_args, **kwargs):
        recorded["view"] = kwargs["artifact_type"] == "intent_hypotheses"
        return SimpleNamespace(viewed_at="2026-02-18T00:00:00Z")

    async def _chain(*_args, **kwargs):
        recorded["chain"] = kwargs["event_type"] == "artifacts_viewed"
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr("app.routers.artifact_views.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.artifact_views.EvaluationRepository.get", _eval)
    monkeypatch.setattr("app.routers.artifact_views.ArtifactViewRepository.record_view", _record)
    monkeypatch.setattr("app.routers.artifact_views.HITLRepository.insert_chain_event", _chain)
    app.dependency_overrides[get_db_session] = _fake_session

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}
    response = client.post(f"/evaluations/{evaluation_id}/artifacts/intent_hypotheses/viewed", headers=headers)

    assert response.status_code == 201
    assert recorded["view"] is True
    assert recorded["chain"] is True
    app.dependency_overrides.clear()

