from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.db import get_db_session  # noqa: E402
from app.main import app  # noqa: E402


def _token(user_id: str, tenant_id: str) -> str:
    return jwt.encode({"sub": user_id, "tenant_id": tenant_id}, "test-secret", algorithm="HS256")


async def _fake_session():
    yield object()


def test_create_evaluation_created_status(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    workspace_id = uuid4()
    job_id = uuid4()
    resume_id = uuid4()
    evaluation_id = uuid4()

    async def _noop(*_args, **_kwargs):
        return None

    async def _create(*_args, **_kwargs):
        return SimpleNamespace(
            id=evaluation_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            job_id=job_id,
            resume_id=resume_id,
            status="created",
            failure_reason_code=None,
            idempotency_key=None,
            created_by=user_id,
            created_at="2026-02-18T00:00:00Z",
        )

    monkeypatch.setattr("app.routers.evaluations.apply_rls_context", _noop)
    monkeypatch.setattr("app.repositories.evaluations.EvaluationRepository.create", _create)

    app.dependency_overrides[get_db_session] = _fake_session
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}

    response = client.post(f"/jobs/{job_id}/resumes/{resume_id}/evaluations", json={}, headers=headers)
    assert response.status_code == 201
    assert response.json()["status"] == "created"

    app.dependency_overrides.clear()

