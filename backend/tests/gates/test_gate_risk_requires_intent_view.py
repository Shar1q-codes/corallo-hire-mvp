from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.services.artifact_gates import gate_reason, is_access_allowed  # noqa: E402


def test_gate_risk_requires_intent_view() -> None:
    blocked = gate_reason(artifact_type="risk_signals", viewed={})
    assert blocked is not None
    assert "Intent Alignment" in blocked
    assert is_access_allowed(artifact_type="risk_signals", viewed={}) is False

    viewed = {"intent_hypotheses": "2026-02-18T00:00:00Z"}
    assert gate_reason(artifact_type="risk_signals", viewed=viewed) is None
    assert is_access_allowed(artifact_type="risk_signals", viewed=viewed) is True

