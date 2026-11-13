import time

from agents.graph import interview_graph
from skill_gap_analyzer import analyze_skill_gap
from roadmap_generator import generate_learning_roadmap
from answer_evaluator import evaluate_answer


def prepare_interview(
    company_name: str,
    job_description: str,
    resume_pdf,
    progress_callback=None,
) -> dict:
    """Run the interview-preparation LangGraph workflow."""

    if not isinstance(company_name, str) or not company_name.strip():
        raise ValueError("Company name cannot be empty.")

    if not isinstance(job_description, str) or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    if resume_pdf is None:
        raise ValueError("Resume PDF is required.")

    initial_state = {
        "company_name": company_name.strip(),
        "job_description": job_description.strip(),
        "resume_pdf": resume_pdf,
    }

    # Map each completed node to the message for the NEXT step that begins
    next_step_message = {
        "extract_resume": f"🌐 Researching {company_name.strip()}...",
        "research_company": "📋 Analyzing job description and requirements...",
        "parse_job": "🔍 Analyzing resume-job skill match...",
        "analyze_skill_gap": "🎯 Generating personalized interview questions...",
        "generate_questions": "✅ Validating interview questions...",
        "validate_questions": "🎉 Finalizing interview preparation...",
    }

    final_state = dict(initial_state)
    start = time.perf_counter()

    print("\n--- [LANGGRAPH] Starting Interview Preparation ---")

    # Initial progress announcement
    if progress_callback:
        progress_callback("📄 Extracting resume information...")

    for output in interview_graph.stream(initial_state):
        for node_name, node_output in output.items():
            print(f"[LANGGRAPH Stream] Node '{node_name}' finished.")

            if progress_callback and node_name in next_step_message:
                progress_callback(next_step_message[node_name])

            if isinstance(node_output, dict):
                final_state.update(node_output)

    elapsed = time.perf_counter() - start
    print(f"--- [LANGGRAPH] Interview Preparation Finished in {elapsed:.2f}s ---\n")

    questions = final_state.get("questions", [])
    job_info = final_state.get("job_info", {})
    resume_text = final_state.get("resume_text", "")

    if not questions:
        raise RuntimeError("The interview workflow completed without generating questions.")

    return {
        "company_name": company_name.strip(),
        "company_research": final_state.get("company_research", ""),
        "job_info": job_info,
        "resume_text": resume_text,
        "questions": questions,
        "skill_gap_report": final_state.get("skill_gap_report"),
    }


def analyze_candidate_skill_gap(resume_text: str, job_info: dict) -> dict:
    """
    Independent Resume-JD skill-gap workflow.

    Runs when the user clicks "Analyze my skill gap". It reuses the
    resume text and parsed job information already stored in the interview
    result, so it does not re-run resume extraction, company research or
    question generation.
    """
    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError("Resume text is empty; cannot analyze skill gap.")

    if not isinstance(job_info, dict) or not job_info:
        raise ValueError("Job information is empty; cannot analyze skill gap.")

    report = analyze_skill_gap(resume_text=resume_text, job_info=job_info)

    if not isinstance(report, dict):
        raise TypeError("Skill gap analyzer returned an unexpected result type.")

    return report


def generate_candidate_roadmap(
    skill_gap_report: dict,
    job_info: dict,
    company_name: str = "",
    timeline_weeks: int = 4,
    use_llm: bool = True,
) -> dict:
    """Generate a structured learning roadmap from the candidate's skill gaps."""
    return generate_learning_roadmap(
        skill_gap_report=skill_gap_report,
        job_info=job_info,
        company_name=company_name,
        timeline_weeks=timeline_weeks,
        use_llm=use_llm,
    )


def evaluate_candidate_answer(
    question: str,
    answer: str,
    job_context: str = "",
    question_type: str = "technical",
) -> dict:
    """Evaluate candidate answer using discriminating rubric scoring."""
    return evaluate_answer(
        question=question,
        answer=answer,
        job_context=job_context,
        question_type=question_type,
    )

