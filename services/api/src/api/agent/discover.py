from typing import Any

DISCOVER_PROMPT_SEQUENCE = [
    "What project or problem made you completely lose track of time recently?",
    "Tell me about a specific technical achievement you are most proud of.",
    "Tell me about a failure in a project and what you learned or changed as a result.",
    "Describe a time you collaborated with others (Situation, Task, Action, Result).",
]


def determine_next_discover_question(message_count: int) -> str:
    """Select the next guiding question in the discovery sequence."""
    idx = (message_count // 2) % len(DISCOVER_PROMPT_SEQUENCE)
    return DISCOVER_PROMPT_SEQUENCE[idx]


def propose_fact_from_user_response(user_text: str) -> dict[str, Any] | None:
    """Analyze user response and propose a candidate fact (ALWAYS confirmed=False)."""
    words = user_text.split()
    if len(words) < 6:
        return None

    # Heuristic determination of kind
    lower = user_text.lower()
    if any(k in lower for k in ["fail", "mistake", "error", "bug", "wrong"]):
        kind = "story_failure"
        title = "Overcoming Challenge: " + " ".join(words[:5]) + "..."
    elif any(k in lower for k in ["built", "created", "launched", "developed", "project"]):
        kind = "story_success"
        title = "Achievement: " + " ".join(words[:5]) + "..."
    elif any(k in lower for k in ["team", "partner", "colleague", "group", "lead"]):
        kind = "story_collaboration"
        title = "Collaboration: " + " ".join(words[:5]) + "..."
    else:
        kind = "experience"
        title = "Experience: " + " ".join(words[:5]) + "..."

    return {
        "kind": kind,
        "title": title[:80],
        "body": user_text,
        "tags": ["agent-discover"],
        "source": "agent",
        "confirmed": False,  # MUST NEVER AUTO-CONFIRM
    }
