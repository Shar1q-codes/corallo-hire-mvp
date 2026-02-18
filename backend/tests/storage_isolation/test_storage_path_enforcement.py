import os
import uuid

import httpx
import pytest

LIVE = os.getenv("LIVE_STORAGE_TESTS", "").lower() == "true"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
USER_A_JWT = os.getenv("USER_A_JWT", "")
TENANT_A = os.getenv("LEAK_TEST_TENANT_A_ID", "")
TENANT_B = os.getenv("LEAK_TEST_TENANT_B_ID", "")

pytestmark = pytest.mark.skipif(
    not (LIVE and SUPABASE_URL and USER_A_JWT and TENANT_A and TENANT_B),
    reason="Set LIVE_STORAGE_TESTS=true with SUPABASE_URL, USER_A_JWT, LEAK_TEST_TENANT_A_ID, LEAK_TEST_TENANT_B_ID.",
)


@pytest.mark.asyncio
async def test_storage_path_enforcement() -> None:
    workspace_id = str(uuid.uuid4())
    resume_id = str(uuid.uuid4())
    filename = "path-enforcement.txt"

    valid_path = f"tenant/{TENANT_A}/workspace/{workspace_id}/resume/{resume_id}/{filename}"
    invalid_path = f"tenant/{TENANT_B}/workspace/{workspace_id}/resume/{resume_id}/{filename}"

    headers = {
        "Authorization": f"Bearer {USER_A_JWT}",
        "Content-Type": "text/plain",
        "x-upsert": "false",
    }

    async with httpx.AsyncClient(base_url=SUPABASE_URL, timeout=60.0) as client:
        ok_resp = await client.post(f"/storage/v1/object/resumes/{valid_path}", headers=headers, content=b"ok")
        assert ok_resp.status_code in {200, 201}, ok_resp.text

        bad_resp = await client.post(f"/storage/v1/object/resumes/{invalid_path}", headers=headers, content=b"bad")
        assert bad_resp.status_code in {400, 401, 403}, bad_resp.text
