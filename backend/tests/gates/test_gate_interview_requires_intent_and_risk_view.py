from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.services.artifact_gates import gate_reason  # noqa: E402


def test_gate_interview_requires_intent_and_risk_view() -> None:
    assert gate_reason(artifact_type="interview_guidance", viewed={}) is not None
    assert gate_reason(artifact_type="interview_guidance", viewed={"intent_hypotheses": "ts"}) is not None
    assert gate_reason(
        artifact_type="interview_guidance",
        viewed={"intent_hypotheses": "ts", "risk_signals": "ts"},
    ) is None

