from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.append(str(Path(__file__).resolve().parents[3] / "backend"))

from app.schemas.hitl import AckCreate  # noqa: E402


def test_ack_rejects_boilerplate_content() -> None:
    with pytest.raises(ValidationError):
        AckCreate(
            acknowledgement_type="counter_signal_ack",
            subject_ref_type="general",
            subject_ref_id=None,
            content_text="acknowledged acknowledged acknowledged acknowledged acknowledged acknowledged",
            decision_mode="validate_in_interview",
        )

