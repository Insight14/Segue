import json
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from api.config import get_settings


class BaseLlmProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a complete text response."""
        ...

    @abstractmethod
    def stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        """Stream chunks of response."""
        ...


class MockLlmProvider(BaseLlmProvider):
    """Deterministic mock provider for CI testing and evals."""

    def __init__(self, predefined_response: str | None = None) -> None:
        self.predefined_response = predefined_response

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        if self.predefined_response:
            return self.predefined_response

        # Default intelligent response generator for Discover / Prep
        if "PRODUCE_TALKING_POINTS_JSON" in prompt or "talking points" in prompt.lower():
            pitch = (
                "Hi, I am a software engineer focused on distributed systems and smart wearables."
            )
            weakness = (
                "Earlier I took on too many tasks at once without delegating; "
                "now I timebox and review scope weekly."
            )
            return json.dumps(
                {
                    "pitch_30s": pitch,
                    "stories": [
                        {
                            "title": "Smart Glasses Coach",
                            "situation": "Conversational stutter at networking events.",
                            "action": "Built heads-up display coach using Whisper and local LLM.",
                            "result": "Cut response freeze time by 75%.",
                            "fact_id": "mock-fact-1",
                        }
                    ],
                    "questions_to_ask": [
                        "What is the team's biggest challenge in production?",
                        "How do you evaluate new engineering technologies?",
                        "What does mentorship look like on your team?",
                        "What are the key goals for this quarter?",
                        "How does your team handle technical debt?",
                    ],
                    "icebreakers": [
                        "Did you see the recent open-source release of faster whisper models?",
                        "How has the turnout been at the event today?",
                        "Have you had a chance to try any of the robotics demos upstairs?",
                    ],
                    "if_asked_about_weakness": weakness,
                    "gaps": ["No specific notes found for this company's latest cloud migration."],
                }
            )

        return (
            "That sounds like a defining experience. What specific challenge "
            "did you overcome during that project?"
        )

    async def stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        full_text = await self.generate(prompt, system_prompt)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            yield chunk


_mock_provider_instance: MockLlmProvider | None = None


def get_llm_provider() -> BaseLlmProvider:
    global _mock_provider_instance
    settings = get_settings()
    if settings.ENVIRONMENT in ["local", "test"] or not getattr(settings, "GROQ_API_KEY", None):
        if _mock_provider_instance is None:
            _mock_provider_instance = MockLlmProvider()
        return _mock_provider_instance
    return MockLlmProvider()


def set_mock_llm_provider(mock: MockLlmProvider | None) -> None:
    global _mock_provider_instance
    _mock_provider_instance = mock
