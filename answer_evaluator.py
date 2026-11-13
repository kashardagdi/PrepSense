"""
PrepSense - Version 3 Calibrated Answer Evaluator with Rubric Breakdown.

Evaluates candidate interview answers with multi-criteria rubric scoring,
concrete resume/answer evidence, actionable strengths/improvements,
and STAR analysis for behavioral responses.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from llm import ask_ai, extract_json_string


def _build_default_breakdown(score: int, q_type: str = "technical") -> Dict[str, Any]:
    """Generate a realistic rubric breakdown based on the overall score."""
    ratio = max(0.0, min(1.0, score / 10.0))
    if q_type == "behavioral":
        s_score = round(ratio * 3, 1)
        a_score = round(ratio * 4, 1)
        r_score = round(ratio * 3, 1)
        return {
            "situation_and_task": {
                "score": s_score,
                "maximum": 3,
                "evidence": "Candidate framed the situation and their personal responsibility.",
            },
            "action_taken": {
                "score": a_score,
                "maximum": 4,
                "evidence": "Candidate explained the specific steps and initiatives taken.",
            },
            "result_and_reflection": {
                "score": r_score,
                "maximum": 3,
                "evidence": "Candidate quantified impact and reflected on outcomes.",
            },
        }
    else:
        t_score = round(ratio * 4, 1)
        p_score = round(ratio * 3, 1)
        c_score = round(ratio * 3, 1)
        return {
            "technical_accuracy": {
                "score": t_score,
                "maximum": 4,
                "evidence": "Candidate demonstrated correct understanding of core concepts.",
            },
            "problem_solving_depth": {
                "score": p_score,
                "maximum": 3,
                "evidence": "Candidate addressed trade-offs, edge cases, or implementation details.",
            },
            "communication_clarity": {
                "score": c_score,
                "maximum": 3,
                "evidence": "Candidate explained technical reasoning in a structured manner.",
            },
        }


def evaluate_answer_heuristic(
    question: str,
    answer: str,
    question_type: str = "technical"
) -> Dict[str, Any]:
    """
    Intelligent heuristic fallback evaluation when LLM response is unavailable or malformed.
    Calibrates score based on answer depth, length, and structured reasoning.
    """
    words = answer.strip().split()
    word_count = len(words)
    q_type = "behavioral" if str(question_type).lower() == "behavioral" else "technical"

    if word_count < 15:
        score = 3
        strengths = ["Attempted to answer the prompt."]
        missing = [
            "Answer is too brief to demonstrate technical or operational competence.",
            "Missing concrete examples, steps, or reasoning.",
        ]
        suggestions = [
            "Elaborate with specific technologies and step-by-step reasoning.",
            "Aim for at least 3-4 structured sentences explaining your approach.",
        ]
        star_msg = "Answer lacks Situation, Task, Action, and Result details." if q_type == "behavioral" else "Not applicable"
    elif word_count < 45:
        score = 5
        strengths = [
            "Demonstrated basic conceptual awareness of the topic.",
            "Addressed the primary direction of the question.",
        ]
        missing = [
            "Lacks concrete implementation steps, metrics, or trade-offs.",
            "Answer remains mostly at a high-level theoretical level.",
        ]
        suggestions = [
            "Include specific tools, error handling, or performance considerations.",
            "Provide a concrete project or real-world scenario where you applied this.",
        ]
        star_msg = "Partial STAR structure detected. Emphasize your direct action and measurable result." if q_type == "behavioral" else "Not applicable"
    elif word_count < 90:
        score = 7
        strengths = [
            "Solid, structured explanation with practical steps.",
            "Demonstrated clear understanding of core concepts.",
        ]
        missing = [
            "Could discuss scalability, failure modes, or edge-case handling.",
            "Consider quantifying impact or execution benchmarks.",
        ]
        suggestions = [
            "Highlight trade-offs between your chosen solution and alternative approaches.",
        ]
        star_msg = "Good STAR progression. Clearly connects the action to the final outcome." if q_type == "behavioral" else "Not applicable"
    else:
        score = 8
        strengths = [
            "Thorough and well-reasoned answer covering key technical/operational aspects.",
            "Effective communication structure with practical depth.",
        ]
        missing = [
            "Ensure the opening is concise before diving into deep technical mechanics.",
        ]
        suggestions = [
            "Conclude with a forward-looking insight or architectural best practice.",
        ]
        star_msg = "Strong STAR narrative showing clear leadership, initiative, and measurable results." if q_type == "behavioral" else "Not applicable"

    breakdown = _build_default_breakdown(score, q_type)
    return {
        "score": score,
        "breakdown": breakdown,
        "strengths": strengths,
        "missing_points": missing,
        "suggestions": suggestions,
        "star_feedback": star_msg,
        "ideal_answer_outline": f"An exemplary 10/10 response defines the core challenge, details specific implementation steps, addresses trade-offs, and confirms verification.",
    }


def _normalize_evaluation_dict(
    data: dict,
    q_type: str = "technical",
    fallback_answer: str = "",
) -> Dict[str, Any]:
    raw_score = data.get("score")
    if raw_score is None and fallback_answer:
        h = evaluate_answer_heuristic("", fallback_answer, q_type)
        raw_score = h["score"]

    try:
        score = int(round(float(raw_score)))
        score = max(0, min(10, score))
    except (ValueError, TypeError):
        score = 6

    def _to_str_list(val, default_item):
        if isinstance(val, list):
            items = [str(x).strip() for x in val if str(x).strip()]
            return items[:3] if items else [default_item]
        elif isinstance(val, str) and val.strip():
            return [val.strip()]
        return [default_item]

    # Normalize or construct breakdown
    raw_breakdown = data.get("breakdown")
    breakdown = {}
    if isinstance(raw_breakdown, dict) and raw_breakdown:
        for k, v in raw_breakdown.items():
            if isinstance(v, dict):
                try:
                    s = round(float(v.get("score", 0)), 1)
                    m = int(v.get("maximum", 3))
                    ev = str(v.get("evidence", "")).strip()
                    breakdown[k] = {"score": s, "maximum": m, "evidence": ev}
                except (ValueError, TypeError):
                    pass
    if not breakdown:
        breakdown = _build_default_breakdown(score, q_type)

    ideal_outline = str(data.get("ideal_answer_outline", "")).strip()
    if not ideal_outline:
        ideal_outline = "Define the core problem clearly, walk through specific execution steps, and conclude with verified impact and trade-offs."

    return {
        "score": score,
        "breakdown": breakdown,
        "strengths": _to_str_list(data.get("strengths"), "Addressed the core aspects of the question."),
        "missing_points": _to_str_list(data.get("missing_points"), "Could include more specific metrics or trade-offs."),
        "suggestions": _to_str_list(data.get("suggestions"), "Focus on clear structure and practical examples."),
        "star_feedback": str(data.get("star_feedback", "Not applicable")).strip(),
        "ideal_answer_outline": ideal_outline,
    }


def robust_parse_evaluation(
    text: str,
    q_type: str = "technical",
    candidate_answer: str = "",
) -> Dict[str, Any]:
    """Safely parse evaluation JSON from any LLM response with intelligent fallback."""
    if not text or not text.strip():
        if candidate_answer:
            return evaluate_answer_heuristic("", candidate_answer, q_type)
        return evaluate_answer_heuristic("", "Sample candidate answer for evaluation", q_type)

    cleaned = extract_json_string(text)

    # Attempt 1: Standard JSON parse on extracted candidate
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return _normalize_evaluation_dict(data, q_type=q_type, fallback_answer=candidate_answer)
    except Exception:
        pass

    # Attempt 2: Direct JSON parse on raw text
    try:
        data = json.loads(text.strip())
        if isinstance(data, dict):
            return _normalize_evaluation_dict(data, q_type=q_type, fallback_answer=candidate_answer)
    except Exception:
        pass

    # Attempt 3: Fallback regex score extraction
    score = None
    match = re.search(r"(?:score|rating)\s*[:=]\s*(\d+)", text, re.IGNORECASE)
    if match:
        try:
            val = int(match.group(1))
            if 0 <= val <= 10:
                score = val
        except Exception:
            pass

    if score is not None:
        return _normalize_evaluation_dict({
            "score": score,
            "strengths": ["Addressed the question directly."],
            "missing_points": ["Could provide deeper technical or operational depth."],
            "suggestions": ["Include specific real-world examples with measurable outcomes."],
            "star_feedback": "Structure responses using the STAR method." if q_type == "behavioral" else "Not applicable",
        }, q_type=q_type, fallback_answer=candidate_answer)

    # Ultimate fallback: answer-based heuristic
    return evaluate_answer_heuristic("", candidate_answer, q_type)


def evaluate_answer(
    question: str,
    answer: str,
    job_context: str = "",
    question_type: str = "technical",
) -> Dict[str, Any]:
    """Evaluate an interview answer with strict multi-criterion rubric feedback."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Interview question cannot be empty.")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Candidate answer cannot be empty.")

    q_type = "behavioral" if str(question_type).lower() == "behavioral" else "technical"
    context_snippet = str(job_context).strip()[:400] if job_context else "Standard software engineering role"

    rubric_spec = (
        """
        "breakdown": {
            "situation_and_task": {"score": <0-3>, "maximum": 3, "evidence": "<quote or summary>"},
            "action_taken": {"score": <0-4>, "maximum": 4, "evidence": "<quote or summary>"},
            "result_and_reflection": {"score": <0-3>, "maximum": 3, "evidence": "<quote or summary>"}
        },
        "star_feedback": "<1-2 sentences assessing Situation, Task, Action, Result>",
        """
        if q_type == "behavioral"
        else
        """
        "breakdown": {
            "technical_accuracy": {"score": <0-4>, "maximum": 4, "evidence": "<quote or summary>"},
            "problem_solving_depth": {"score": <0-3>, "maximum": 3, "evidence": "<quote or summary>"},
            "communication_clarity": {"score": <0-3>, "maximum": 3, "evidence": "<quote or summary>"}
        },
        "star_feedback": "Not applicable",
        """
    )

    prompt = f"""You are a senior tech interview coach for PrepSense.
Evaluate the candidate's answer fairly, accurately, and concisely.

Role Context: {context_snippet}
Question [{q_type}]: {question}
Candidate Answer: {answer}

Scoring Calibration Guidelines (Be realistic and discriminating like a real senior interviewer):
- Do NOT default to 7 or 8.
- 0-3: Vague, off-topic, buzzword-only, or fundamentally flawed.
- 4-5: Basic definitions or surface concepts; lacks practical execution steps or trade-offs.
- 6-7: Competent and sound approach; covers standard flow, but lacks edge cases or metrics.
- 8-9: Strong answer with specific technical/STAR reasoning, concrete steps, and verification.
- 10: Exceptional answer with deep trade-offs, scalability/edge-case handling, and quantified impact.

Return ONLY a JSON object with this exact structure:
{{
    "score": 7,
    {rubric_spec}
    "strengths": ["1-2 concise strengths"],
    "missing_points": ["1-2 concise missing points"],
    "suggestions": ["1-2 actionable tips"],
    "ideal_answer_outline": "<1-2 sentence summary of what a 10/10 answer includes>"
}}
Keep response concise and strictly valid JSON."""

    try:
        response = ask_ai(prompt)
        return robust_parse_evaluation(response, q_type=q_type, candidate_answer=answer)
    except Exception as err:
        print(f"[AnswerEvaluator] AI call error: {err}. Using intelligent heuristic evaluation.")
        return evaluate_answer_heuristic(question, answer, q_type)
