from datetime import datetime, timezone
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


def test_status_endpoint_shape(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    evaluation_id = uuid4()

    async def _noop(*_args, **_kwargs):
        return None

    async def _eval(*_args, **_kwargs):
        return SimpleNamespace(id=evaluation_id)

    async def _available(*_args, **_kwargs):
        return {"intent_hypotheses", "risk_signals"}

    async def _view_map(*_args, **_kwargs):
        return {"intent_hypotheses": datetime(2026, 2, 18, tzinfo=timezone.utc)}

    monkeypatch.setattr("app.routers.artifact_views.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.artifact_views.EvaluationRepository.get", _eval)
    monkeypatch.setattr("app.routers.artifact_views.ArtifactRepository.get_available_types", _available)
    monkeypatch.setattr("app.routers.artifact_views.ArtifactViewRepository.get_latest_view_map", _view_map)
    app.dependency_overrides[get_db_session] = _fake_session

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}
    response = client.get(f"/evaluations/{evaluation_id}/artifacts/status", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"available", "viewed", "gates"}
    assert set(body["available"].keys()) == {"intent_hypotheses", "risk_signals", "interview_guidance"}
    assert set(body["viewed"].keys()) == {"intent_hypotheses", "risk_signals", "interview_guidance"}
    assert set(body["gates"].keys()) == {"risk_signals_unlocked", "interview_guidance_unlocked"}
    app.dependency_overrides.clear()

