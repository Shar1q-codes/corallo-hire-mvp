import os
import re
from typing import Any

import httpx
import pytest

FORBIDDEN_PATTERN = re.compile(
    r"\b(hire|hired|reject|rejected|shortlist|shortlisted|offer|offered|advanced|best|top|score|rank|fit|overall|in summary)\b",
    re.IGNORECASE,
)
PERCENT_PATTERN = re.compile(r"\b\d{1,3}\s?%\b")


def _iter_strings(node: Any):
    if isinstance(node, dict):
        for value in node.values():
            yield from _iter_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_strings(value)
    elif isinstance(node, str):
        yield node


@pytest.mark.skipif(os.getenv("LIVE_TESTS", "").lower() != "true", reason="LIVE_TESTS is not enabled")
def test_live_run_drift_guard() -> None:
    base_url = os.getenv("LIVE_BASE_URL", "http://localhost:8000")
    token = os.getenv("LIVE_BEARER_TOKEN", "")
    evaluation_id = os.getenv("LIVE_EVALUATION_ID", "")

    if not token or not evaluation_id:
        pytest.skip("LIVE_BEARER_TOKEN and LIVE_EVALUATION_ID are required.")

    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(timeout=60.0) as client:
        run_resp = client.post(f"{base_url}/evaluations/{evaluation_id}/run", headers=headers)
        assert run_resp.status_code in (200, 503)
        if run_resp.status_code == 503:
            pytest.skip("Provider temporarily unavailable.")

        for artifact_type in ("intent_hypotheses", "risk_signals", "interview_guidance"):
            view_resp = client.post(f"{base_url}/evaluations/{evaluation_id}/artifacts/{artifact_type}/viewed", headers=headers)
            assert view_resp.status_code in (201, 200)
            artifact_resp = client.get(f"{base_url}/evaluations/{evaluation_id}/artifacts/{artifact_type}", headers=headers)
            assert artifact_resp.status_code == 200
            payload = artifact_resp.json().get("content_json", {})
            for text in _iter_strings(payload):
                assert FORBIDDEN_PATTERN.search(text) is None
                assert PERCENT_PATTERN.search(text) is None

