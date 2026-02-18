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


def test_workspace_crud_flow(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    workspace_id = uuid4()

    async def _noop(*_args, **_kwargs):
        return None

    async def _create(*_args, **_kwargs):
        return SimpleNamespace(
            id=workspace_id,
            tenant_id=tenant_id,
            name="Workspace A",
            created_by=user_id,
            created_at="2026-02-18T00:00:00Z",
        )

    async def _list(*_args, **_kwargs):
        return [
            SimpleNamespace(
                id=workspace_id,
                tenant_id=tenant_id,
                name="Workspace A",
                created_by=user_id,
                created_at="2026-02-18T00:00:00Z",
            )
        ]

    async def _get(*_args, **_kwargs):
        return SimpleNamespace(
            id=workspace_id,
            tenant_id=tenant_id,
            name="Workspace A",
            created_by=user_id,
            created_at="2026-02-18T00:00:00Z",
        )

    async def _delete(*_args, **_kwargs):
        return True

    monkeypatch.setattr("app.routers.workspaces.apply_rls_context", _noop)
    monkeypatch.setattr("app.repositories.workspaces.WorkspaceRepository.create", _create)
    monkeypatch.setattr("app.repositories.workspaces.WorkspaceRepository.list", _list)
    monkeypatch.setattr("app.repositories.workspaces.WorkspaceRepository.get", _get)
    monkeypatch.setattr("app.repositories.workspaces.WorkspaceRepository.update_name", _get)
    monkeypatch.setattr("app.repositories.workspaces.WorkspaceRepository.delete", _delete)

    app.dependency_overrides[get_db_session] = _fake_session
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}

    create_response = client.post("/workspaces", json={"name": "Workspace A"}, headers=headers)
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Workspace A"

    list_response = client.get("/workspaces", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/workspaces/{workspace_id}", headers=headers)
    assert get_response.status_code == 200

    patch_response = client.patch(f"/workspaces/{workspace_id}", json={"name": "Workspace B"}, headers=headers)
    assert patch_response.status_code == 200

    delete_response = client.delete(f"/workspaces/{workspace_id}", headers=headers)
    assert delete_response.status_code == 204

    app.dependency_overrides.clear()

