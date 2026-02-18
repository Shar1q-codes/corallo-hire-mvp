import os
import uuid

import httpx
import pytest

LIVE = os.getenv("LIVE_STORAGE_TESTS", "").lower() == "true"
API_BASE_URL = os.getenv("API_BASE_URL", "")
USER_A_JWT = os.getenv("USER_A_JWT", "")
USER_B_JWT = os.getenv("USER_B_JWT", "")

pytestmark = pytest.mark.skipif(
    not (LIVE and API_BASE_URL and USER_A_JWT and USER_B_JWT),
    reason="Set LIVE_STORAGE_TESTS=true with API_BASE_URL, USER_A_JWT, USER_B_JWT.",
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_signed_url_tenant_isolation() -> None:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=60.0) as client:
        ws_resp = await client.post("/workspaces", headers=_auth(USER_A_JWT), json={"name": "Storage Isolation Workspace"})
        assert ws_resp.status_code == 201, ws_resp.text
        workspace_id = ws_resp.json()["id"]

        files = {"file": ("signed-url.txt", b"signed-url-test", "text/plain")}
        resume_resp = await client.post(
            f"/workspaces/{workspace_id}/resumes",
            headers=_auth(USER_A_JWT),
            files=files,
        )
        assert resume_resp.status_code == 201, resume_resp.text
        resume_id = resume_resp.json()["resume_id"]

        own_url_resp = await client.get(f"/resumes/{resume_id}/download-url", headers=_auth(USER_A_JWT))
        assert own_url_resp.status_code == 200, own_url_resp.text
        assert "url" in own_url_resp.json()

        other_url_resp = await client.get(f"/resumes/{resume_id}/download-url", headers=_auth(USER_B_JWT))
        assert other_url_resp.status_code in {403, 404}, other_url_resp.text
