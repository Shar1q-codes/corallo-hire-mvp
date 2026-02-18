from app.validators.types import ArtifactType


def gate_reason(
    *,
    artifact_type: str,
    viewed: dict[str, object],
) -> str | None:
    if artifact_type == ArtifactType.INTENT_HYPOTHESES.value:
        return None
    if artifact_type == ArtifactType.RISK_SIGNALS.value:
        if ArtifactType.INTENT_HYPOTHESES.value not in viewed:
            return "Risk Signals require Intent Alignment to be reviewed first."
        return None
    if artifact_type == ArtifactType.INTERVIEW_GUIDANCE.value:
        has_intent = ArtifactType.INTENT_HYPOTHESES.value in viewed
        has_risk = ArtifactType.RISK_SIGNALS.value in viewed
        if not has_intent or not has_risk:
            return "Interview Guidance requires Intent Alignment and Risk Signals to be reviewed first."
        return None
    return "Artifact type is not supported."


def is_access_allowed(*, artifact_type: str, viewed: dict[str, object]) -> bool:
    return gate_reason(artifact_type=artifact_type, viewed=viewed) is None

