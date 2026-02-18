from pathlib import Path
import sys
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


def test_ack_insert_returns_404_when_eval_not_in_tenant_scope(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    evaluation_id = uuid4()

    async def _noop(*_args, **_kwargs):
        return None

    async def _missing_context(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.routers.hitl.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.hitl.EvaluationRepository.get_context", _missing_context)
    app.dependency_overrides[get_db_session] = _fake_session

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}
    response = client.post(
        f"/evaluations/{evaluation_id}/acknowledgements",
        headers=headers,
        json={
            "acknowledgement_type": "counter_signal_ack",
            "subject_ref_type": "risk_item",
            "subject_ref_id": "risk:1",
            "content_text": "This risk note is acknowledged with explicit context and validation intent.",
            "decision_mode": "validate_in_interview",
        },
    )

    assert response.status_code == 404
    app.dependency_overrides.clear()
