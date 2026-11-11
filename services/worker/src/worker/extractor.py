import re
from typing import Any

SECTION_PATTERNS = {
    "education": [r"\beducation\b", r"\bacademics\b", r"\buniversity\b"],
    "experience": [r"\bexperience\b", r"\bwork history\b", r"\bemployment\b"],
    "skill": [r"\bskills\b", r"\btechnical skills\b", r"\bcompetencies\b"],
    "project": [r"\bprojects\b", r"\bkey projects\b", r"\bpersonal projects\b"],
}


def extract_candidate_facts(resume_text: str) -> list[dict[str, Any]]:
    """Extract proposed profile facts from resume text.

    CRITICAL RULE: All proposed facts MUST have confirmed=False and source='resume'.
    """
    candidate_facts: list[dict[str, Any]] = []
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]

    current_section = "other"
    section_buffers: dict[str, list[str]] = {
        "education": [],
        "experience": [],
        "skill": [],
        "project": [],
        "other": [],
    }

    for line in lines:
        lower_line = line.lower()
        matched_section = None
        for sec, patterns in SECTION_PATTERNS.items():
            if any(re.search(p, lower_line) for p in patterns) and len(line) < 40:
                matched_section = sec
                break

        if matched_section:
            current_section = matched_section
        else:
            section_buffers[current_section].append(line)

    # 1. Process Education
    if section_buffers["education"]:
        edu_body = "\n".join(section_buffers["education"][:5])
        first_line = section_buffers["education"][0]
        candidate_facts.append(
            {
                "kind": "education",
                "title": f"Education: {first_line[:80]}",
                "body": edu_body,
                "tags": ["education", "resume"],
                "source": "resume",
                "confirmed": False,  # MUST NEVER AUTO-CONFIRM
            }
        )

    # 2. Process Experience
    if section_buffers["experience"]:
        # Split into blocks of 1-3 lines
        exp_lines = section_buffers["experience"]
        chunk_size = 4
        for i in range(0, min(len(exp_lines), 12), chunk_size):
            chunk = exp_lines[i : i + chunk_size]
            title = chunk[0][:80]
            candidate_facts.append(
                {
                    "kind": "experience",
                    "title": f"Experience: {title}",
                    "body": "\n".join(chunk),
                    "tags": ["experience", "resume"],
                    "source": "resume",
                    "confirmed": False,  # MUST NEVER AUTO-CONFIRM
                }
            )

    # 3. Process Skills
    if section_buffers["skill"]:
        skill_text = ", ".join(section_buffers["skill"][:6])
        candidate_facts.append(
            {
                "kind": "skill",
                "title": "Technical Skills",
                "body": skill_text,
                "tags": ["skills", "resume"],
                "source": "resume",
                "confirmed": False,  # MUST NEVER AUTO-CONFIRM
            }
        )

    # 4. Process Projects
    if section_buffers["project"]:
        proj_lines = section_buffers["project"]
        chunk_size = 3
        for i in range(0, min(len(proj_lines), 6), chunk_size):
            chunk = proj_lines[i : i + chunk_size]
            title = chunk[0][:80]
            candidate_facts.append(
                {
                    "kind": "story_success",
                    "title": f"Project: {title}",
                    "body": "\n".join(chunk),
                    "tags": ["project", "resume"],
                    "source": "resume",
                    "confirmed": False,  # MUST NEVER AUTO-CONFIRM
                }
            )

    # Fallback if no sections recognized
    if not candidate_facts and lines:
        candidate_facts.append(
            {
                "kind": "other",
                "title": "Resume Overview",
                "body": "\n".join(lines[:10]),
                "tags": ["resume"],
                "source": "resume",
                "confirmed": False,  # MUST NEVER AUTO-CONFIRM
            }
        )

    return candidate_facts
