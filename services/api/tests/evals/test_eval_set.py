import uuid

import pytest

from api.agent.guardrails import (
    GuardrailViolationError,
    check_safe_topics,
    validate_character_limits,
    validate_talking_points_guardrails,
)
from api.agent.prep import generate_talking_points_for_user
from api.agent.provider import MockLlmProvider, set_mock_llm_provider
from api.models.fact import ProfileFact
from api.models.profile import Profile
from api.schemas.agent import TalkingPointsContent, TalkingPointStory

# 20 Distinct Evaluation Test Cases
EVAL_CASES = [
    {
        "id": "eval_01_standard_cs_student",
        "headline": "CS Junior at Berkeley",
        "facts": [
            ("education", "B.S. CS", "GPA 3.8, took operating systems and networking"),
            ("experience", "Backend Intern", "Wrote asyncio Python microservices"),
            (
                "story_failure",
                "Failed DB migration",
                "Broke staging DB; learned to test down-migrations",
            ),
        ],
        "notes": "Stripe career fair booth",
    },
    {
        "id": "eval_02_career_changer",
        "headline": "Former Mechanical Engineer turned Software Developer",
        "facts": [
            ("experience", "Robotics Designer", "Created CAD models and hardware prototypes"),
            ("skill", "Python and Rust", "Proficient in systems programming"),
        ],
        "notes": "Autonomous vehicle startup",
    },
    {
        "id": "eval_03_embedded_systems",
        "headline": "Embedded Systems Enthusiast",
        "facts": [
            ("experience", "Firmware Intern", "Programmed STM32 and ESP32 with FreeRTOS"),
            ("story_success", "Sensor Mesh", "Built wireless mesh with 99.9% uptime"),
        ],
        "notes": "Smart home IoT meetup",
    },
    {
        "id": "eval_04_data_engineer",
        "headline": "Data Pipeline Engineer",
        "facts": [
            ("skill", "Spark and Kafka", "Streamed 10M events per day"),
            ("experience", "Data Platform Co-op", "Managed Airflow DAGs"),
        ],
        "notes": "Fintech networking night",
    },
    {
        "id": "eval_05_devops_sre",
        "headline": "Infrastructure & SRE Intern",
        "facts": [
            ("experience", "Cloud Ops", "Terraform modules for multi-region AWS EKS"),
            (
                "story_failure",
                "Outage post-mortem",
                "Forgot healthcheck; created automated runbook",
            ),
        ],
        "notes": "Datadog recruiter chat",
    },
    {
        "id": "eval_06_mobile_developer",
        "headline": "React Native Mobile Dev",
        "facts": [
            ("experience", "Freelance Mobile Dev", "Published iOS/Android app with 50k downloads"),
            ("skill", "TypeScript & Expo", "Offline sync and TanStack Query"),
        ],
        "notes": "Consumer app expo",
    },
    {
        "id": "eval_07_ml_engineer",
        "headline": "Machine Learning Researcher",
        "facts": [
            ("education", "M.S. in Machine Learning", "Thesis on speech-to-text quantization"),
            (
                "story_success",
                "Whisper optimization",
                "Quantized Whisper model to run at 10x speed",
            ),
        ],
        "notes": "AI conference mixer",
    },
    {
        "id": "eval_08_cybersecurity",
        "headline": "Security Analyst",
        "facts": [
            ("experience", "AppSec Intern", "Threat modeling and SAST pipeline integration"),
            ("skill", "Penetration Testing", "Discovered critical IDOR in university portal"),
        ],
        "notes": "InfoSec job fair",
    },
    {
        "id": "eval_09_fullstack_web",
        "headline": "Full-Stack Engineer",
        "facts": [
            ("experience", "Fullstack dev", "FastAPI backend with Next.js frontend"),
            ("skill", "PostgreSQL", "Query optimization and index tuning"),
        ],
        "notes": "SaaS startup mixer",
    },
    {
        "id": "eval_10_hardware_hacker",
        "headline": "Hardware & Wearables Creator",
        "facts": [
            ("story_success", "HUD Glasses", "Soldered OLED and beamsplitter onto 3D glasses"),
            ("skill", "PCB Design", "KiCad layout for dual-layer USB-C power board"),
        ],
        "notes": "Maker Faire hardware booth",
    },
    {
        "id": "eval_11_bioinformatics",
        "headline": "Computational Biology Student",
        "facts": [
            ("education", "Bioinformatics B.S.", "Genomics sequence alignment algorithms"),
            ("experience", "Lab Assistant", "Automated pipeline for sequencing results"),
        ],
        "notes": "HealthTech recruiting",
    },
    {
        "id": "eval_12_game_developer",
        "headline": "Game Engine Programmer",
        "facts": [
            ("experience", "Indie Studio Intern", "Built custom entity-component-system in C++"),
            ("skill", "Vulkan & Shaders", "Graphics optimization"),
        ],
        "notes": "Game Developers Conference",
    },
    {
        "id": "eval_13_qa_automation",
        "headline": "QA & Automation Engineer",
        "facts": [
            (
                "experience",
                "Test Engineer",
                "Wrote 500+ integration tests in Pytest and Playwright",
            ),
            ("skill", "CI/CD", "GitHub Actions test matrix runner"),
        ],
        "notes": "Enterprise software mixer",
    },
    {
        "id": "eval_14_distributed_systems",
        "headline": "Distributed Systems Engineer",
        "facts": [
            ("experience", "Storage Intern", "Raft consensus implementation in Go"),
            (
                "story_failure",
                "Split brain test",
                "Fixed heartbeat timeouts under network partition",
            ),
        ],
        "notes": "Cloud infrastructure summit",
    },
    {
        "id": "eval_15_open_source_contributor",
        "headline": "Open Source Maintainer",
        "facts": [
            ("story_success", "OSS maintainer", "Merged 40 PRs in major Python async library"),
            ("skill", "Code Review", "Community management and bug triage"),
        ],
        "notes": "PyCon networking",
    },
    {
        "id": "eval_16_product_engineer",
        "headline": "Product-Minded Engineer",
        "facts": [
            ("experience", "Growth Intern", "A/B testing sign-up flows; boosted conversion by 12%"),
            ("skill", "User Analytics", "Event-driven instrumentation"),
        ],
        "notes": "Early-stage incubator showcase",
    },
    {
        "id": "eval_17_audio_dsp",
        "headline": "Audio & Speech DSP Developer",
        "facts": [
            ("experience", "Acoustics Intern", "Beamforming microphone array algorithms"),
            ("skill", "Digital Signal Processing", "Low-latency RNNoise implementation"),
        ],
        "notes": "Wearables conference",
    },
    {
        "id": "eval_18_minimal_profile",
        "headline": "First-year CS Student",
        "facts": [
            ("education", "CS Freshman", "Introductory Python and Data Structures"),
        ],
        "notes": "Campus club fair",
    },
    {
        "id": "eval_19_veteran_engineer",
        "headline": "Senior Platform Lead",
        "facts": [
            ("experience", "Staff Architect", "Designed multi-tenant Kubernetes platform"),
            (
                "story_success",
                "Zero-downtime migration",
                "Migrated 200 databases without data loss",
            ),
        ],
        "notes": "Executive leadership roundtable",
    },
    {
        "id": "eval_20_researcher",
        "headline": "HCI Researcher",
        "facts": [
            ("education", "Ph.D. Candidate", "User trust in real-time conversational agents"),
            (
                "experience",
                "Research Fellow",
                "User studies with 100 participants wearing smart glasses",
            ),
        ],
        "notes": "CHI Human-Computer Interaction Expo",
    },
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", EVAL_CASES, ids=[c["id"] for c in EVAL_CASES])
async def test_eval_case_schema_and_grounding(case: dict) -> None:
    """Eval case: Verify schema validation, no hallucinated facts, and guardrail compliance."""
    user_id = uuid.uuid4()
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user_id,
        headline=case["headline"],
        status="Active",
        goals="Make strong connections",
        tone_preference="professional and approachable",
    )

    confirmed_facts: list[ProfileFact] = []
    for kind, title, body in case["facts"]:
        confirmed_facts.append(
            ProfileFact(
                id=uuid.uuid4(),
                user_id=user_id,
                kind=kind,
                title=title,
                body=body,
                tags=["eval", kind],
                source="user",
                confirmed=True,
            )
        )

    # Execute prep generator with mocked provider
    set_mock_llm_provider(MockLlmProvider())
    result = await generate_talking_points_for_user(
        profile=profile,
        confirmed_facts=confirmed_facts,
        notes=case["notes"],
    )

    # 1. Schema Validation (Pydantic check)
    assert isinstance(result, TalkingPointsContent)
    assert len(result.pitch_30s) > 10
    assert len(result.questions_to_ask) <= 5
    assert len(result.icebreakers) <= 3
    assert len(result.stories) <= 3

    # 2. No Fabricated Facts (Grounding check)
    confirmed_ids = {str(f.id) for f in confirmed_facts}
    for story in result.stories:
        if story.fact_id:
            assert (
                story.fact_id in confirmed_ids
            ), f"Story '{story.title}' references unconfirmed fact_id '{story.fact_id}'"

    # 3. Guardrail: Character limits on short prompts
    for q in result.questions_to_ask:
        assert validate_character_limits(q, max_chars=120)

    # 4. Guardrail: Safe topics compliance
    for icebreaker in result.icebreakers:
        check_safe_topics(icebreaker)


def test_guardrails_reject_fabricated_fact_id() -> None:
    """Guardrail catches and rejects stories claiming non-existent or unconfirmed facts."""
    invalid_content = TalkingPointsContent(
        pitch_30s="I am an engineer.",
        stories=[
            TalkingPointStory(
                title="Invented Story",
                situation="Fake",
                action="Did something",
                result="Achieved something",
                fact_id="fabricated-fact-999",
            )
        ],
        questions_to_ask=["What stack do you use?"],
        icebreakers=["Great day today."],
    )

    confirmed_ids = {"real-fact-1", "real-fact-2"}
    with pytest.raises(
        GuardrailViolationError, match="references unconfirmed or nonexistent fact_id"
    ):
        validate_talking_points_guardrails(invalid_content, confirmed_ids)


def test_guardrails_reject_unsafe_politics_and_tragedies() -> None:
    """Guardrail catches and rejects unsafe topics in icebreakers or pitches."""
    unsafe_content = TalkingPointsContent(
        pitch_30s="I am an engineer interested in the upcoming election and partisan politics.",
        stories=[],
        questions_to_ask=["Who are you voting for?"],
        icebreakers=["Did you see the latest political debate?"],
    )

    with pytest.raises(GuardrailViolationError, match="unsafe topic detected"):
        validate_talking_points_guardrails(unsafe_content, set())
