import re

OUTCOME_PATTERN = re.compile(
    r"\b(hire|hired|reject|rejected|shortlist|shortlisted|offered|advanced)\b",
    re.IGNORECASE,
)


def test_outcome_language_is_detected_in_ack_text() -> None:
    bad_ack_text = "We should hire this profile quickly after review."
    assert OUTCOME_PATTERN.search(bad_ack_text) is not None


def test_neutral_ack_text_has_no_outcome_language() -> None:
    good_ack_text = (
        "The uncertainty around incident communication remains unresolved and should be validated "
        "through concrete examples during interview discussion."
    )
    assert OUTCOME_PATTERN.search(good_ack_text) is None

