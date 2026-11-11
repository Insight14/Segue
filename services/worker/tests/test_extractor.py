from worker.extractor import extract_candidate_facts

SAMPLE_RESUME = """
Jane Doe
jane@example.com | (555) 019-2834

Education
B.S. in Computer Science, University of California, Berkeley (2020-2024)
GPA: 3.9 / 4.0, Dean's Honors List

Experience
Software Engineer Intern at Acme Robotics
Developed low-latency telemetry pipelines in Python and C++.
Reduced serial communication overhead by 40%.

Skills
Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, React Native

Projects
Convo Glasses Assistant
Wearable heads-up display coach for conversations using Whisper and Groq LLMs.
"""


def test_extract_candidate_facts_sections() -> None:
    facts = extract_candidate_facts(SAMPLE_RESUME)
    assert len(facts) >= 3

    # CRITICAL ACCEPTANCE CRITERIA TEST:
    # Nothing is saved as confirmed without user action!
    for fact in facts:
        assert fact["confirmed"] is False, f"Proposed fact {fact['title']} must NOT be confirmed"
        assert fact["source"] == "resume"
        assert fact["kind"] in [
            "education",
            "experience",
            "skill",
            "story_success",
            "other",
        ]
        assert "resume" in fact["tags"]

    kinds = [f["kind"] for f in facts]
    assert "education" in kinds
    assert "experience" in kinds
    assert "skill" in kinds


def test_extract_candidate_facts_empty_or_unstructured() -> None:
    unstructured = "Just a short bio without sections. Passionate about machine learning."
    facts = extract_candidate_facts(unstructured)
    assert len(facts) == 1
    assert facts[0]["confirmed"] is False
    assert facts[0]["source"] == "resume"
