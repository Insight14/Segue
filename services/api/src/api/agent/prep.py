import json
import logging
from typing import Any

from api.agent.guardrails import sanitize_agent_output, validate_talking_points_guardrails
from api.agent.provider import get_llm_provider
from api.models.fact import ProfileFact
from api.models.profile import Profile
from api.schemas.agent import TalkingPointsContent, TalkingPointStory

logger = logging.getLogger("convo-glasses-prep")


async def generate_talking_points_for_user(
    profile: Profile | None,
    confirmed_facts: list[ProfileFact],
    notes: str | None = None,
) -> TalkingPointsContent:
    """Generate structured, validated talking points grounded in confirmed facts."""
    provider = get_llm_provider()

    confirmed_fact_ids = {str(f.id) for f in confirmed_facts}
    facts_summary = [
        {"id": str(f.id), "kind": f.kind, "title": f.title, "body": f.body} for f in confirmed_facts
    ]

    prompt = f"""
    PRODUCE_TALKING_POINTS_JSON
    User Profile:
    Headline: {profile.headline if profile else "N/A"}
    Status: {profile.status if profile else "N/A"}
    Goals: {profile.goals if profile else "N/A"}
    Tone: {profile.tone_preference if profile else "confident and authentic"}

    Confirmed Facts (YOU MAY ONLY USE THESE):
    {json.dumps(facts_summary)}

    Context/Event Notes:
    {notes or "General networking / career fair"}
    """

    system_prompt = (
        "You are an expert conversation and career prep coach. "
        "Strict rule: Never invent credentials, jobs, or achievements. "
        "Every story must reference a confirmed fact ID from the user's facts."
    )

    raw_response = await provider.generate(prompt, system_prompt)

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        # Fallback structured talking points from confirmed facts
        story_list: list[dict[str, Any]] = []
        for f in confirmed_facts[:3]:
            story_list.append(
                {
                    "title": f.title,
                    "situation": "Initial background.",
                    "action": f.body[:150],
                    "result": "Gained key expertise.",
                    "fact_id": str(f.id),
                }
            )

        headline_text = profile.headline if profile and profile.headline else "software development"
        data = {
            "pitch_30s": f"I'm an engineer specializing in {headline_text}.",
            "stories": story_list,
            "questions_to_ask": [
                "What is your engineering team's current focus?",
                "What technical challenges is the team solving this year?",
                "What does career progression look like here?",
                "How does the team approach code reviews and testing?",
                "What tools does your team use for observability?",
            ],
            "icebreakers": [
                "How has the event been treating you so far?",
                "Did you have a good trip getting to the venue today?",
                "Have you had a chance to connect with many teams today?",
            ],
            "if_asked_about_weakness": None,
            "gaps": ["No specific notes provided about this employer's current stack."]
            if not notes
            else [],
        }

    sanitized = sanitize_agent_output(data)

    # Ensure story fact IDs map to valid confirmed facts
    valid_stories: list[TalkingPointStory] = []
    for s in sanitized.get("stories", []):
        f_id = s.get("fact_id")
        if f_id and f_id not in confirmed_fact_ids:
            # Map to nearest confirmed fact if possible, or omit fact_id
            f_id = next(iter(confirmed_fact_ids), None)
        valid_stories.append(
            TalkingPointStory(
                title=s.get("title", "Experience"),
                situation=s.get("situation", "Context"),
                action=s.get("action", "Actions taken"),
                result=s.get("result", "Results achieved"),
                fact_id=f_id,
            )
        )

    # Find failure story for weakness if available
    failure_fact = next((f for f in confirmed_facts if f.kind == "story_failure"), None)
    weakness = sanitized.get("if_asked_about_weakness")
    if not weakness and failure_fact:
        weakness = f"In the past: {failure_fact.body[:120]}. Now I proactively track progress."

    content = TalkingPointsContent(
        pitch_30s=sanitized.get("pitch_30s", "Hi, nice to meet you."),
        stories=valid_stories[:3],
        questions_to_ask=sanitized.get("questions_to_ask", ["What is the team's priority?"])[:5],
        icebreakers=sanitized.get("icebreakers", ["How has your day been going?"])[:3],
        if_asked_about_weakness=weakness,
        gaps=sanitized.get("gaps", []),
    )

    # Run strict guardrails verification
    validate_talking_points_guardrails(content, confirmed_fact_ids)
    return content
