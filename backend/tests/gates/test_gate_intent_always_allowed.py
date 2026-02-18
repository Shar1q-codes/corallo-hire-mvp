from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.services.artifact_gates import gate_reason, is_access_allowed  # noqa: E402


def test_gate_intent_always_allowed() -> None:
    viewed = {}
    assert gate_reason(artifact_type="intent_hypotheses", viewed=viewed) is None
    assert is_access_allowed(artifact_type="intent_hypotheses", viewed=viewed) is True

