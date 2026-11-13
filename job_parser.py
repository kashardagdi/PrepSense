import json
import re
from llm import ask_ai, extract_json_string


def robust_parse_job_info(text: str) -> dict:
    """
    Parse job information from any LLM response format:
    1. Valid JSON
    2. Markdown-fenced JSON (```json ... ```)
    3. Conversational JSON
    4. Plain-text / YAML-style bullet lists (newline OR inline bullets)
    """
    default_structure = {
        "job_title": "",
        "technical_skills": [],
        "tools_and_technologies": [],
        "responsibilities": [],
        "qualifications": [],
    }

    if not text or not text.strip():
        return default_structure

    cleaned = extract_json_string(text)

    # Attempt 1: Standard JSON parse from extracted candidate
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return _normalize_job_dict(parsed)
    except Exception:
        pass

    # Attempt 2: Direct JSON parse on raw text
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict):
            return _normalize_job_dict(parsed)
    except Exception:
        pass

    # Attempt 3: Fallback regex parser for multi-line YAML/plain-text headers
    result = {
        "job_title": "",
        "technical_skills": [],
        "tools_and_technologies": [],
        "responsibilities": [],
        "qualifications": [],
    }

    title_match = re.search(r"job_title\s*:\s*[\"']?([^\n,\"]+)", text, re.IGNORECASE)
    if title_match:
        result["job_title"] = title_match.group(1).strip()

    sections = [
        ("technical_skills", r"(?:technical_skills|technical skills)\s*:"),
        ("tools_and_technologies", r"(?:tools_and_technologies|tools and technologies)\s*:"),
        ("responsibilities", r"responsibilities\s*:"),
        ("qualifications", r"qualifications\s*:"),
    ]

    found_headers = []
    for key, pattern in sections:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            found_headers.append((m.start(), m.end(), key))

    found_headers.sort(key=lambda x: x[0])

    for i, (start_pos, end_pos, key) in enumerate(found_headers):
        next_start = found_headers[i + 1][0] if i + 1 < len(found_headers) else len(text)
        section_body = text[end_pos:next_start].strip()

        # Split on newline bullets OR inline " - " patterns
        items = re.split(r"\n\s*[-*\u2022]\s*|\s+-\s+", section_body)
        cleaned_items = [
            item.strip().strip('"').strip("'").strip(",").strip("-").strip()
            for item in items
            if item.strip() and len(item.strip()) > 2
        ]
        result[key] = cleaned_items

    # Attempt 4: Last-resort line-by-line YAML parser
    # Handles: "technical_skills: - Python - Java - C++" all on one line
    if not any(result[k] for k in result if k != "job_title"):
        result = _parse_yaml_oneline(text, result)

    return result


def _parse_yaml_oneline(text: str, result: dict) -> dict:
    """
    Handles YAML where all bullets are inline on one line.
    e.g. 'technical_skills: - Python - Java - C++'
    """
    key_map = {
        "technical_skills": "technical_skills",
        "technical skills": "technical_skills",
        "tools_and_technologies": "tools_and_technologies",
        "tools and technologies": "tools_and_technologies",
        "responsibilities": "responsibilities",
        "qualifications": "qualifications",
        "job_title": "job_title",
    }
    for line in text.splitlines():
        line = line.strip()
        for label, field in key_map.items():
            if line.lower().startswith(label + ":"):
                value = line[len(label) + 1:].strip()
                if field == "job_title":
                    result["job_title"] = value.strip('"').strip("'")
                else:
                    # Split on inline ' - ' bullets
                    items = re.split(r"\s+-\s+|-\s+|\n|,\s*", value)
                    cleaned = [
                        i.strip().strip(",").strip('"').strip("'")
                        for i in items if i.strip() and len(i.strip()) > 2
                    ]
                    if cleaned:
                        result[field] = cleaned
                break
    return result


def _normalize_job_dict(data: dict) -> dict:
    required_keys = [
        "job_title",
        "technical_skills",
        "tools_and_technologies",
        "responsibilities",
        "qualifications",
    ]
    result = {}
    for k in required_keys:
        val = data.get(k)
        if k == "job_title":
            result[k] = str(val).strip() if val else ""
        else:
            if isinstance(val, list):
                items = [str(item).strip() for item in val if item]
            elif isinstance(val, str) and val.strip():
                items = [item.strip() for item in val.split("\n") if item.strip()]
            else:
                items = []

            # Keep lists focused on the most critical items (prevents prompt explosion)
            if k == "technical_skills":
                result[k] = items[:6]
            elif k == "tools_and_technologies":
                result[k] = items[:4]
            else:
                result[k] = items[:5]
    return result


def parse_job_description(job_description: str) -> dict:
    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    job_text = job_description.strip()[:2500]

    prompt = f"""Analyze the following job description and extract information.

Return ONLY a JSON object with this exact structure:
{{
    "job_title": "Role title",
    "technical_skills": ["skill 1", "skill 2"],
    "tools_and_technologies": ["tool 1", "tool 2"],
    "responsibilities": ["duty 1", "duty 2"],
    "qualifications": ["requirement 1"]
}}

Rules:
- Return ONLY the JSON object. No markdown, no explanation.
- Keep lists concise (top 4-6 items per category).

Job description:
{job_text}
"""

    response = ask_ai(prompt)

    job_info = robust_parse_job_info(response)

    return job_info


if __name__ == "__main__":
    sample_job = """
Backend Developer Intern.

Required skills: Python, PostgreSQL, and FastAPI.

Tools: Git, Docker, and Postman.

Responsibilities: Build and test REST API endpoints,
debug backend services, and write unit tests.

Qualifications: Currently pursuing a Computer Science
degree, basic knowledge of databases, and 0-1 years
of experience.
"""

    result = parse_job_description(sample_job)

    print(json.dumps(result, indent=2))
