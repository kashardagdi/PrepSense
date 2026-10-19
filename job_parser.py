
import json
from llm import ask_ai


def parse_job_description(job_description: str) -> dict:
    # Check that the input is not empty
    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    
    prompt = f"""
    Analyze the following job description and extract information
    using only evidence from the supplied text.

    Return ONLY valid JSON using exactly these keys:
    {{
        "job_title": "string",
        "technical_skills": ["string"],
        "tools_and_technologies": ["string"],
        "responsibilities": ["string"],
        "qualifications": ["string"]
    }}

    Extraction rules:
    - job_title: Extract the stated role title.
    - technical_skills: Include explicitly required programming,
      database, API, and computer science skills.
    - tools_and_technologies: Include named tools, platforms,
      languages, frameworks, databases, and technologies.
    - responsibilities: Include duties explicitly described.
    - qualifications: Include explicitly stated education,
      experience, certifications, and other candidate requirements.
    - A skill or technology may appear in both relevant lists.
    - Do not invent qualifications or responsibilities.
    - If a category has no supporting information, return [].
    - If the job title is missing, return an empty string.
    - Return no Markdown fences or extra explanation.

    Job description:
    {job_description}
    """

    response = ask_ai(prompt)

    try:
        job_info = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError(
            "The AI did not return valid JSON. "
            f"Raw response: {response}"
        ) from error

    # Check that all expected fields exist
    required_keys = [
        "job_title",
        "technical_skills",
        "tools_and_technologies",
        "responsibilities",
        "qualifications",
    ]

    for key in required_keys:
        if key not in job_info:
            raise ValueError(f"Missing required field: {key}")

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
