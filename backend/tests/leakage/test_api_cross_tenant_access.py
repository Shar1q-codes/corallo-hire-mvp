import os
import uuid

import httpx
import pytest

LIVE = os.getenv("LIVE_API_TESTS", "").lower() == "true"
API_BASE_URL = os.getenv("API_BASE_URL", "")
USER_A_JWT = os.getenv("USER_A_JWT", "")
USER_B_JWT = os.getenv("USER_B_JWT", "")

pytestmark = pytest.mark.skipif(
    not (LIVE and API_BASE_URL and USER_A_JWT and USER_B_JWT),
    reason="Set LIVE_API_TESTS=true with API_BASE_URL, USER_A_JWT, USER_B_JWT.",
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_api_cross_tenant_access() -> None:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=60.0) as client:
        ws_resp = await client.post("/workspaces", headers=_auth(USER_A_JWT), json={"name": "Tenant A Workspace"})
        assert ws_resp.status_code == 201, ws_resp.text
        workspace_id = ws_resp.json()["id"]

        job_resp = await client.post(
            f"/workspaces/{workspace_id}/jobs",
            headers=_auth(USER_A_JWT),
            json={"title": "Tenant A Job", "description": "x" * 320, "recruiter_notes": ""},
        )
        assert job_resp.status_code == 201, job_resp.text
        job_id = job_resp.json()["id"]

        files = {"file": ("resume.txt", b"tenant-a-resume", "text/plain")}
        resume_resp = await client.post(
            f"/workspaces/{workspace_id}/resumes",
            headers=_auth(USER_A_JWT),
            files=files,
        )
        assert resume_resp.status_code == 201, resume_resp.text
        resume_id = resume_resp.json()["resume_id"]

        eval_resp = await client.post(
            f"/jobs/{job_id}/resumes/{resume_id}/evaluations",
            headers=_auth(USER_A_JWT),
            json={"idempotency_key": str(uuid.uuid4())},
        )
        assert eval_resp.status_code == 201, eval_resp.text
        evaluation_id = eval_resp.json()["id"]

        b_endpoints = [
            f"/workspaces/{workspace_id}",
            f"/jobs/{job_id}",
            f"/resumes/{resume_id}",
            f"/evaluations/{evaluation_id}",
            f"/evaluations/{evaluation_id}/artifacts/status",
        ]

        for endpoint in b_endpoints:
            resp = await client.get(endpoint, headers=_auth(USER_B_JWT))
            assert resp.status_code in {403, 404}, f"Unexpected status for {endpoint}: {resp.status_code}"
            body = resp.text.lower()
            assert "tenant a" not in body
            assert workspace_id not in body
            assert job_id not in body
            assert resume_id not in body
            assert evaluation_id not in body

        run_resp = await client.post(f"/evaluations/{evaluation_id}/run", headers=_auth(USER_B_JWT))
        assert run_resp.status_code in {403, 404}, run_resp.text
