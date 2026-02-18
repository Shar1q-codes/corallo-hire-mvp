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


def test_decision_boundary_check_requires_risk_reference_when_risk_artifact_exists(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    evaluation_id = uuid4()

    async def _noop(*_args, **_kwargs):
        return None

    async def _eval_row(*_args, **_kwargs):
        return SimpleNamespace(id=evaluation_id)

    async def _list_acks(*_args, **_kwargs):
        return [
            SimpleNamespace(
                acknowledgement_type="counter_signal_ack",
                content_text="Counter signal noted with explicit uncertainty and interview validation intent.",
                subject_ref_type="general",
                subject_ref_id="general:1",
            ),
            SimpleNamespace(
                acknowledgement_type="validation_gap_declaration",
                content_text="Validation gap declared with concrete evidence plan for interview follow-up.",
                subject_ref_type="general",
                subject_ref_id="general:2",
            ),
        ]

    async def _has_risk(*_args, **_kwargs):
        return True

    async def _insert_event(*_args, **_kwargs):
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr("app.routers.hitl.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.hitl.EvaluationRepository.get", _eval_row)
    monkeypatch.setattr("app.routers.hitl.HITLRepository.list_acknowledgements_for_evaluation", _list_acks)
    monkeypatch.setattr("app.routers.hitl.HITLRepository.has_risk_signals_artifact", _has_risk)
    monkeypatch.setattr("app.routers.hitl.HITLRepository.insert_chain_event", _insert_event)
    app.dependency_overrides[get_db_session] = _fake_session

    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}
    response = client.post(f"/evaluations/{evaluation_id}/decision-boundary-check", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["eligible"] is False
    assert any("risk item" in message for message in body["missing"])
    app.dependency_overrides.clear()
