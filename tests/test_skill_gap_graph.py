import json
import sys
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from agents.graph import interview_graph
def run_real_graph_test():

    resume_path = (
        r"D:\Internship Practise school 1\Resume_for_salesforce.pdf"
    )

    job_description = """
    Backend Developer Intern

    Technical Skills:
    Python, PostgreSQL, FastAPI

    Tools and Technologies:
    Git, Docker, Postman

    Responsibilities:
    - Build and test REST API endpoints.
    - Debug backend services.
    - Write unit tests.

    Qualifications:
    - Computer Science degree.
    - Basic database knowledge.
    - 0-1 years of experience.
    """

    result = interview_graph.invoke({
        "company_name": "Amazon",
        "job_description": job_description,
        "resume_pdf": resume_path,
    })

    print("\n===== FINAL GRAPH STATE =====")

    print("\nCurrent Step:")
    print(result.get("current_step"))

    print("\nSkill Gap Report:")
    print(json.dumps(
        result.get("skill_gap_report"),
        indent=4,
        ensure_ascii=False
    ))

    print("\nQuestions Validated:")
    print(result.get("questions_validated"))

    print("\nGenerated Questions:")
    print(json.dumps(
        result.get("questions"),
        indent=4,
        ensure_ascii=False
    ))


if __name__ == "__main__":
    run_real_graph_test()