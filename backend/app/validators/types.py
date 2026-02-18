from enum import Enum


class RoleType(str, Enum):
    INTENT = "intent"
    RISK = "risk"
    ASSUMPTION = "assumption"
    INTERVIEW = "interview"


class ArtifactType(str, Enum):
    INTENT_HYPOTHESES = "intent_hypotheses"
    RISK_SIGNALS = "risk_signals"
    INTERVIEW_GUIDANCE = "interview_guidance"


class FailureCode(str, Enum):
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    FORBIDDEN_LANGUAGE = "FORBIDDEN_LANGUAGE"
    PROBABILITY_LANGUAGE = "PROBABILITY_LANGUAGE"
    ANTI_COMPRESSION_FAIL = "ANTI_COMPRESSION_FAIL"
    EXCERPT_RESISTANCE_FAIL = "EXCERPT_RESISTANCE_FAIL"
    RISK_NAMING_INVALID = "RISK_NAMING_INVALID"

