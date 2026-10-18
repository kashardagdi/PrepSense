
from llm import ask_ai

def parse_job_description(job_description: str) -> str:
    prompt = f"""
    Analyze the following job description.

    Extract:
    1. Job title
    2. Required technical skills
    3. Tools and technologies
    4. Main responsibilities
    5. Important qualifications

    Return the result in clear, organized sections.

    Job description:
    {job_description}
    """

    return ask_ai(prompt)


if __name__ == "__main__":
    sample_job = """
    Python Developer Intern.
    Required skills: Python, SQL, REST APIs, Git,
    and basic data structures.
    Responsibilities: Build backend services
    and debug code.
    """

    result = parse_job_description(sample_job)
    print(result)
