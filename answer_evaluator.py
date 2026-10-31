
import json
from llm import ask_ai

def evaluate_answer(
    question: str,
    answer: str,
    job_context: str,
    question_type: str = "technical",
) -> dict:
    """Evaluate an interview answer and return structured feedback."""

    if not question.strip():
        raise ValueError("Interview question cannot be empty.")

    if not answer.strip():
        raise ValueError("Candidate answer cannot be empty.")

    if question_type not in ("technical", "behavioral"):
        raise ValueError(
            "Question type must be technical or behavioral."
        )

    prompt = f"""
    You are an interview coach for PrepSense.

    Evaluate the candidate's answer fairly and constructively.

    Interview question:
    {question}

    Question type:
    {question_type}

    Job context:
    {job_context}

    Candidate's answer:
    {answer}

    Evaluate:
    - Correctness and relevance
    - Completeness
    - Clarity and structure
    - Reasoning and practical examples

    For behavioral questions, assess STAR:
    Situation, Task, Action, and Result.
    For technical questions, use "Not applicable" for STAR feedback.

    Return ONLY valid JSON with exactly these keys:
    {{
        "score": 0,
        "strengths": ["string"],
        "missing_points": ["string"],
        "suggestions": ["string"],
        "star_feedback": "string"
    }}

    Rules:
    - score must be an integer from 0 to 10.
    - strengths, missing_points, and suggestions must be lists of strings.
    - star_feedback must be a string.
    - Do not include Markdown fences or extra explanation.
    """

    response = ask_ai(prompt)

    try:
        feedback = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"The AI did not return valid JSON: {response}"
        ) from error

    # Validate the top-level structure.
    if not isinstance(feedback, dict):
        raise ValueError("Feedback must be a JSON object.")

    required_keys = [
        "score",
        "strengths",
        "missing_points",
        "suggestions",
        "star_feedback",
    ]

    for key in required_keys:
        if key not in feedback:
            raise ValueError(f"Missing required field: {key}")

    # Validate the score.
    score = feedback["score"]

    if type(score) is not int or not 0 <= score <= 10:
        raise ValueError("Score must be an integer from 0 to 10.")

    # Validate the text fields.
    for key in ("strengths", "missing_points", "suggestions"):
        value = feedback[key]

        if not isinstance(value, list):
            raise ValueError(f"'{key}' must be a list.")

        if not all(
            isinstance(item, str) and item.strip()
            for item in value
        ):
            raise ValueError(
                f"Every item in '{key}' must be a non-empty string."
            )

    if not isinstance(feedback["star_feedback"], str):
        raise ValueError("'star_feedback' must be a string.")

    return feedback



if __name__ == "__main__":

 question = (
    "Tell me about a time you solved a difficult problem "
    "while working in a team."
)

answer = """
During a college project, our team had a problem because
the API was returning incorrect results. I was responsible
for debugging the backend. I checked the API response,
found an incorrect database query, and fixed it. After
testing the endpoint, the results became correct and our
team completed the project on time.
"""

job_context = """
Role: Backend Developer Intern
Required skills: Python, PostgreSQL, FastAPI.
Responsibilities: Build REST APIs, debug backend services,
and write unit tests.
"""
print("Evaluating behavioral interview answer...\n")
feedback = evaluate_answer(
    question=question,
    answer=answer,
    job_context=job_context,
    question_type="behavioral",
)
print("BEHAVIORAL ANSWER EVALUATION")
print("=" * 40)
print(json.dumps(feedback, indent=2))