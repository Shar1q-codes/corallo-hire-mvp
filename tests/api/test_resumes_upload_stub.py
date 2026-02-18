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


def test_resume_upload_path_and_signed_url(monkeypatch) -> None:
    tenant_id = str(uuid4())
    user_id = str(uuid4())
    workspace_id = uuid4()
    resume_id = uuid4()

    async def _noop(*_args, **_kwargs):
        return None

    async def _upload(*_args, **_kwargs):
        return None

    async def _create(*_args, **kwargs):
        return SimpleNamespace(
            id=resume_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            file_object_path=kwargs["file_object_path"],
            original_filename="resume.txt",
            mime_type="text/plain",
            size_bytes=12,
            extracted_text=None,
            created_by=user_id,
            created_at="2026-02-18T00:00:00Z",
        )

    async def _get(*_args, **_kwargs):
        return SimpleNamespace(
            id=resume_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            file_object_path=(
                f"tenant/{tenant_id}/workspace/{workspace_id}/resume/{resume_id}/resume.txt"
            ),
            original_filename="resume.txt",
            mime_type="text/plain",
            size_bytes=12,
            extracted_text=None,
            created_by=user_id,
            created_at="2026-02-18T00:00:00Z",
        )

    async def _signed_url(*_args, **_kwargs):
        return "https://example.com/signed"

    monkeypatch.setattr("app.routers.resumes.apply_rls_context", _noop)
    monkeypatch.setattr("app.routers.resumes.upload_resume_file", _upload)
    monkeypatch.setattr("app.repositories.resumes.ResumeRepository.create", _create)
    monkeypatch.setattr("app.repositories.resumes.ResumeRepository.get", _get)
    monkeypatch.setattr("app.routers.resumes.create_signed_download_url", _signed_url)

    app.dependency_overrides[get_db_session] = _fake_session
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token(user_id, tenant_id)}"}

    upload_response = client.post(
        f"/workspaces/{workspace_id}/resumes",
        headers=headers,
        files={"file": ("resume.txt", b"hello world", "text/plain")},
    )
    assert upload_response.status_code == 201
    path = upload_response.json()["file_object_path"]
    assert path.startswith(f"tenant/{tenant_id}/workspace/{workspace_id}/resume/")

    signed_response = client.get(f"/resumes/{resume_id}/download-url", headers=headers)
    assert signed_response.status_code == 200
    assert signed_response.json()["url"] == "https://example.com/signed"

    app.dependency_overrides.clear()

