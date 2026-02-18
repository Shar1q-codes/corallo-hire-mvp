from pathlib import Path
import sys

import jwt
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[2] / "backend"))

from app.main import app  # noqa: E402


def _token(payload: dict) -> str:
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_non_health_without_auth_fails_closed() -> None:
    client = TestClient(app)
    response = client.get("/workspaces")
    assert response.status_code == 401


def test_non_health_without_tenant_claim_fails_closed() -> None:
    client = TestClient(app)
    bearer = _token({"sub": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"})
    response = client.get("/workspaces", headers={"Authorization": f"Bearer {bearer}"})
    assert response.status_code == 401

