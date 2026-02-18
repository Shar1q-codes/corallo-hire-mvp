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


def test_ack_insert_creates_chain_event(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    evaluation_id = uuid4()
    workspace_id = uuid4()
    job_id = uuid4()
    resume_id = uuid4()
    recorded_events: list[str] = []

    async def _noop(*_args, **_kwargs):
        return None

    async def _context(*_args, **_kwargs):
        return SimpleNamespace(
            evaluation=SimpleNamespace(
                id=evaluation_id,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                job_id=job_id,
                resume_id=resume_id,
            ),
            job=SimpleNamespace(),
            resume=SimpleNamespace(),
        )

    async def _insert_ack(*_args, **_kwargs):
        return SimpleNamespace(id=uuid4())

    async def _insert_event(*_args, **kwargs):
        recorded_events.append(kwargs["event_type"])
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr("app.routers.hitl.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.hitl.EvaluationRepository.get_context", _context)
    monkeypatch.setattr("app.routers.hitl.HITLRepository.insert_acknowledgement", _insert_ack)
    monkeypatch.setattr("app.routers.hitl.HITLRepository.insert_chain_event", _insert_event)
    app.dependency_overrides[get_db_session] = _fake_session

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}
    response = client.post(
        f"/evaluations/{evaluation_id}/acknowledgements",
        headers=headers,
        json={
            "acknowledgement_type": "validation_gap_declaration",
            "subject_ref_type": "general",
            "subject_ref_id": None,
            "content_text": "Validation evidence is currently incomplete and must be collected directly in interview.",
            "decision_mode": "validate_in_interview",
        },
    )

    assert response.status_code == 201
    assert "acknowledgement_recorded" in recorded_events
    app.dependency_overrides.clear()
