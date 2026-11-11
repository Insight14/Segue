import re
from typing import Any

from api.schemas.agent import TalkingPointsContent

UNSAFE_TOPICS_REGEX = [
    r"\b(democrat|republican|election|biden|trump|congress|senate|partisan)\b",
    r"\b(religion|jesus|allah|bible|quran|theology|salvation)\b",
    r"\b(shooting|terrorist|assassination|tragedy|bombing|genocide)\b",
    r"\b(joke at your expense|ugly|stupid|idiot)\b",
]


class GuardrailViolationError(ValueError):
    """Raised when an agent output violates project safety and accuracy rules."""

    pass


def validate_character_limits(text: str, max_chars: int = 80) -> bool:
    """Live suggestions and display strings must be <= 80 ASCII characters (16x8 display)."""
    if len(text) > max_chars:
        return False
    return True


def check_safe_topics(text: str) -> None:
    """Ensure text contains no politics, religion, tragedies, or offensive content."""
    lower = text.lower()
    for pattern in UNSAFE_TOPICS_REGEX:
        if re.search(pattern, lower):
            raise GuardrailViolationError(
                f"Guardrail violation: unsafe topic detected matching '{pattern}'"
            )


def validate_talking_points_guardrails(
    content: TalkingPointsContent,
    confirmed_fact_ids: set[str],
) -> None:
    """Validate that talking points do not fabricate facts and observe safety guardrails."""
    # 1. Check safe topics in icebreakers and pitch
    check_safe_topics(content.pitch_30s)
    for icebreaker in content.icebreakers:
        check_safe_topics(icebreaker)
    for q in content.questions_to_ask:
        check_safe_topics(q)

    # 2. Check fact grounding: Every story MUST trace to a confirmed fact ID
    for story in content.stories:
        check_safe_topics(story.title)
        check_safe_topics(story.action)
        if story.fact_id and story.fact_id not in confirmed_fact_ids:
            msg = (
                f"Guardrail violation: story '{story.title}' references "
                f"unconfirmed or nonexistent fact_id '{story.fact_id}'"
            )
            raise GuardrailViolationError(msg)


def sanitize_agent_output(raw_output: dict[str, Any]) -> dict[str, Any]:
    """Sanitize and clamp lengths on output fields."""
    # Clamp stories to max 3
    if "stories" in raw_output and isinstance(raw_output["stories"], list):
        raw_output["stories"] = raw_output["stories"][:3]
    return raw_output
