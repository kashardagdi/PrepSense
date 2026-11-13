from langgraph.graph import StateGraph, START, END

from agents.state import InterviewState
from agents.nodes import (
    extract_resume_node,
    research_company_node,
    parse_job_node,
    analyze_skill_gap_node,
    generate_questions_node,
    validate_questions_node,
)


def create_interview_graph():
    builder = StateGraph(InterviewState)

    # Register interview preparation nodes
    builder.add_node("extract_resume", extract_resume_node)
    builder.add_node("research_company", research_company_node)
    builder.add_node("parse_job", parse_job_node)
    builder.add_node("analyze_skill_gap", analyze_skill_gap_node)
    builder.add_node("generate_questions", generate_questions_node)
    builder.add_node("validate_questions", validate_questions_node)

    # Define the interview preparation workflow
    builder.add_edge(START, "extract_resume")
    builder.add_edge("extract_resume", "research_company")
    builder.add_edge("research_company", "parse_job")
    builder.add_edge("parse_job", "analyze_skill_gap")
    builder.add_edge("analyze_skill_gap", "generate_questions")
    builder.add_edge("generate_questions", "validate_questions")
    builder.add_edge("validate_questions", END)

    return builder.compile()


interview_graph = create_interview_graph()
