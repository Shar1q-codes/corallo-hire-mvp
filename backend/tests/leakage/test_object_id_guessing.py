import os
import uuid

import httpx
import pytest

LIVE = os.getenv("LIVE_API_TESTS", "").lower() == "true"
API_BASE_URL = os.getenv("API_BASE_URL", "")
USER_A_JWT = os.getenv("USER_A_JWT", "")

pytestmark = pytest.mark.skipif(
    not (LIVE and API_BASE_URL and USER_A_JWT),
    reason="Set LIVE_API_TESTS=true with API_BASE_URL and USER_A_JWT.",
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_object_id_guessing_returns_not_found_or_forbidden() -> None:
    random_ids = [str(uuid.uuid4()) for _ in range(5)]

    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        for rid in random_ids:
            endpoints = [
                f"/workspaces/{rid}",
                f"/jobs/{rid}",
                f"/resumes/{rid}",
                f"/evaluations/{rid}",
                f"/evaluations/{rid}/artifacts/status",
            ]
            for endpoint in endpoints:
                resp = await client.get(endpoint, headers=_auth(USER_A_JWT))
                assert resp.status_code in {403, 404}, f"Unexpected status for {endpoint}: {resp.status_code}"
                assert rid not in resp.text
