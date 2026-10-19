
import json

from llm import ask_ai
from job_parser import parse_job_description
from tools.company_research import (
    search_company,
    summarize_company_research,
)


def generate_questions(
    job_info: dict,
    company_research: str,
) -> list:
    """Generate and validate eight company-aware interview questions."""

    prompt = f"""
    You are an interview preparation assistant for PrepSense.

    Generate exactly 8 interview questions using the job information
    and company research provided below.

    Requirements:
    - Generate exactly 5 technical questions.
    - Generate exactly 3 behavioral questions.
    - Make questions relevant to the job role and its required skills.
    - Use company research where relevant.
    - Do not invent unsupported company facts.
    - Avoid duplicate questions.
    - Do not provide answers.

    Return ONLY valid JSON with this structure:
    {{
        "questions": [
            {{
                "question": "The interview question",
                "type": "technical",
                "reason": "Why this question is relevant"
            }}
        ]
    }}

    Job information:
    {json.dumps(job_info, indent=2)}

    Company research:
    {company_research}
    """

    print("Asking Qwen to generate questions...")
    response = ask_ai(prompt)

    # Attempt to parse the original response.
    try:
        data = json.loads(response)

    except json.JSONDecodeError:
        print("The response was not valid JSON. Trying one repair...")

        repair_prompt = f"""
        Produce a complete, valid JSON object for interview questions.

        Requirements:
        - Exactly 8 questions.
        - Exactly 5 technical and 3 behavioral questions.
        - Every question must have a non-empty question, type, and reason.
        - The type must be technical or behavioral.
        - Return only JSON, without Markdown fences.

        Use this structure:
        {{
            "questions": [
                {{
                    "question": "A complete interview question",
                    "type": "technical",
                    "reason": "Why it is relevant"
                }}
            ]
        }}

        Repair the following response:
        {response}
        """

        repaired_response = ask_ai(repair_prompt)

        try:
            data = json.loads(repaired_response)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Qwen returned invalid JSON even after the repair attempt. "
                "Please run the script again."
            ) from error

    # Validate the JSON structure.
    if not isinstance(data, dict):
        raise ValueError("The AI response must be a JSON object.")

    questions = data.get("questions")

    if not isinstance(questions, list) or len(questions) != 8:
        raise ValueError("The AI must return exactly 8 questions.")

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise ValueError(
                f"Question {index} must be a JSON object."
            )

        for key in ("question", "type", "reason"):
            value = question.get(key)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Question {index} needs a non-empty '{key}' field."
                )

        if question["type"] not in ("technical", "behavioral"):
            raise ValueError(
                f"Question {index} has an invalid type."
            )

    # Check the requested distribution.
    technical_count = sum(
        question["type"] == "technical" for question in questions
    )
    behavioral_count = sum(
        question["type"] == "behavioral" for question in questions
    )

    if technical_count != 5 or behavioral_count != 3:
        raise ValueError(
            "Expected 5 technical and 3 behavioral questions, "
            f"but received {technical_count} technical and "
            f"{behavioral_count} behavioral."
        )

    return questions


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

    try:
        print("\nSTEP 1: Parsing the job description...")
        job_info = parse_job_description(sample_job)
        print("Job description parsed successfully.")

        print("\nSTEP 2: Researching Microsoft...")
        company_results = search_company("Microsoft")
        company_research = summarize_company_research(company_results)
        print("Company research completed.")

        print("\nSTEP 3: Generating interview questions...")
        questions = generate_questions(job_info, company_research)

        print("\n" + "=" * 55)
        print("       PREPSENSE INTERVIEW QUESTIONS")
        print("=" * 55)

        for number, question in enumerate(questions, start=1):
            print(f"\n{number}. [{question['type'].upper()}]")
            print(question["question"])
            print(f"   Reason: {question['reason']}")

        print("\n" + "=" * 55)
        print("Success! All 8 questions passed validation.")

    except (ValueError, RuntimeError) as error:
        print(f"\nPrepSense encountered a problem: {error}")
