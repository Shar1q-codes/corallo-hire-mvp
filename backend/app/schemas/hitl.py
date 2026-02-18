from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AcknowledgementType(str, Enum):
    COUNTER_SIGNAL_ACK = "counter_signal_ack"
    VALIDATION_GAP_DECLARATION = "validation_gap_declaration"
    OVERRIDE_OR_DISAGREEMENT = "override_or_disagreement"


class SubjectRefType(str, Enum):
    INTENT_ITEM = "intent_item"
    RISK_ITEM = "risk_item"
    ASSUMPTION_ITEM = "assumption_item"
    INTERVIEW_FOCUS_AREA = "interview_focus_area"
    GENERAL = "general"


class DecisionMode(str, Enum):
    VALIDATE_IN_INTERVIEW = "validate_in_interview"
    SKIP_VALIDATION = "skip_validation"
    DISAGREE = "disagree"
    ACCEPT_WITH_CONTEXT = "accept_with_context"


_DENYLIST = {
    "acknowledged",
    "reviewed",
    "ok",
    "done",
    "looks good",
    "understood",
}


def _unique_word_count(text: str) -> int:
    words = [w.lower() for w in text.split() if w.strip()]
    return len(set(words))


class AckCreate(BaseModel):
    acknowledgement_type: AcknowledgementType
    subject_ref_type: SubjectRefType
    subject_ref_id: str | None = Field(default=None, max_length=255)
    content_text: str = Field(min_length=30, max_length=2000)
    decision_mode: DecisionMode

    @field_validator("content_text")
    @classmethod
    def validate_content_text(cls, value: str) -> str:
        normalized = " ".join(value.split()).strip()
        if normalized.lower() in _DENYLIST:
            raise ValueError("content_text is too generic. Provide explicit reasoning.")
        if _unique_word_count(normalized) < 6:
            raise ValueError("content_text must include sufficient unique reasoning detail.")
        return normalized


class AckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    job_id: UUID
    resume_id: UUID
    evaluation_id: UUID
    acknowledgement_type: AcknowledgementType
    subject_ref_type: SubjectRefType
    subject_ref_id: str | None
    content_text: str
    decision_mode: DecisionMode
    created_at: datetime
    created_by: UUID


class ChainEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    evaluation_id: UUID
    actor_user_id: UUID
    event_type: str
    detail_json: dict
    created_at: datetime


class ArtifactsViewedCreate(BaseModel):
    artifact_types: list[str] = Field(default_factory=list)


class DecisionBoundaryCheckRead(BaseModel):
    eligible: bool
    missing: list[str]

