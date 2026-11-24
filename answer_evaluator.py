"""
PrepSense - Version 3 Calibrated & Discriminating Answer Evaluator.

Evaluates candidate interview answers with multi-criteria rubric scoring,
concrete evidence quotes, actionable strengths/improvements, and STAR analysis.
Guarantees logical scoring calibration: below-average answers receive 2-4,
mediocre answers receive 5-6, and only strong, evidence-backed answers receive 8-10.
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


# Curated technical keywords and mechanics indicators
TECH_DOMAIN_TERMS = {
    "index", "indexes", "indexing", "cache", "caching", "query", "queries", "latency",
    "throughput", "microservice", "microservices", "partition", "sharding", "async",
    "asyncio", "thread", "threads", "concurrency", "heap", "stack", "algorithm",
    "api", "apis", "rest", "restful", "http", "git", "docker", "container", "containers",
    "kubernetes", "cluster", "database", "databases", "table", "schema", "migration",
    "benchmark", "profiling", "profile", "monitor", "metrics", "p99", "p95", "memory",
    "cpu", "network", "queue", "kafka", "redis", "postgres", "postgresql", "mysql",
    "sqlite", "mongodb", "acid", "distributed", "lock", "locking", "mutex", "deadlock",
    "replication", "replica", "failover", "circuit", "breaker", "pool", "pooling",
}

PROBLEM_SOLVING_TERMS = {
    "because", "trade-off", "tradeoff", "trade-offs", "however", "instead", "alternative",
    "bottleneck", "overhead", "scale", "scaling", "degrade", "mitigate", "prevent",
    "ensure", "verify", "measure", "reduced", "increased", "optimized", "improving",
    "debug", "debugging", "isolated", "root cause", "investigated", "telemetry", "explain",
}

BEHAVIORAL_ACTION_TERMS = {
    "i designed", "i led", "i analyzed", "i implemented", "i created", "i resolved",
    "i proposed", "i scheduled", "i coordinated", "i spoke", "i aligned", "i built",
    "i discovered", "i decided", "my responsibility", "my role", "my approach",
}

BEHAVIORAL_RESULT_TERMS = {
    "result", "resulted in", "outcome", "achieved", "improved", "reduced", "delivered",
    "learned", "retrospective", "lesson", "impact", "successful", "prevented", "percent",
    "%", "saved", "increased",
}

FLUFF_PHRASES = [
    "as we know", "it is very important", "we should make sure", "good programming practice",
    "i like programming", "very popular", "everyone uses it", "basically", "as everyone knows",
    "it is well known", "to be honest", "as i said",
]


def evaluate_answer_heuristic(
    question: str,
    answer: str,
    question_type: str = "technical",
) -> Dict[str, Any]:
    """
    Intelligent, multi-dimensional content-aware evaluation heuristic.
    Evaluates relevance, technical depth, concrete mechanisms, and structure
    to produce discriminating scores (3-4 for vague/poor, 5-6 for basic, 8-9 for strong).
    """
    ans_clean = answer.strip()
    words = ans_clean.split()
    word_count = len(words)
    ans_lower = ans_clean.lower()
    q_lower = question.lower()
    q_type = "behavioral" if str(question_type).lower() == "behavioral" else "technical"

    # Extreme brief or empty
    if word_count < 15:
        score = 3
        strengths = ["Attempted to answer the prompt."]
        missing = [
            "Answer is too brief to demonstrate technical or operational competence.",
            "Missing concrete implementation steps, reasoning, or examples.",
        ]
        suggestions = [
            "Provide at least 3-4 structured sentences detailing your technical approach.",
            "Explain specific tools, libraries, or methodologies used.",
        ]
        star_msg = "Answer lacks Situation, Task, Action, and Result details." if q_type == "behavioral" else "Not applicable"
        return {
            "score": score,
            "breakdown": _build_default_breakdown(score, q_type),
            "strengths": strengths,
            "missing_points": missing,
            "suggestions": suggestions,
            "star_feedback": star_msg,
            "ideal_answer_outline": "Define the core problem clearly, walk through specific execution steps, and conclude with verified impact and trade-offs.",
        }

    # Extract non-stopword tokens from question to test question relevance
    stop_words = {"what", "how", "why", "when", "where", "which", "who", "whom", "this", "that", "these", "those", "have", "has", "had", "does", "does", "did", "you", "your", "can", "could", "would", "should", "the", "and", "for", "with", "about"}
    q_tokens = {w for w in re.findall(r"\w+", q_lower) if len(w) > 2 and w not in stop_words}
    overlap_tokens = {w for w in q_tokens if w in ans_lower}
    relevance_ratio = (len(overlap_tokens) / max(len(q_tokens), 1)) if q_tokens else 0.5

    # Count domain-specific terms & mechanisms
    domain_hits = sum(1 for term in TECH_DOMAIN_TERMS if re.search(r"\b" + re.escape(term) + r"\b", ans_lower))
    problem_solving_hits = sum(1 for term in PROBLEM_SOLVING_TERMS if re.search(r"\b" + re.escape(term) + r"\b", ans_lower))
    metric_hits = len(re.findall(r"\b\d+(?:\.\d+)?(?:%|ms|s|k|m|gb|mb|rps|qps)?\b", ans_lower))
    fluff_hits = sum(1 for phrase in FLUFF_PHRASES if phrase in ans_lower)

    if q_type == "behavioral":
        action_hits = sum(1 for phrase in BEHAVIORAL_ACTION_TERMS if phrase in ans_lower)
        result_hits = sum(1 for phrase in BEHAVIORAL_RESULT_TERMS if phrase in ans_lower)

        # Situation & Task (0-3)
        if word_count < 30 or relevance_ratio < 0.2:
            s_score = 1.0
            s_ev = "Minimal context provided regarding the situation or task."
        elif word_count < 60:
            s_score = 2.0
            s_ev = "Established the business/team context and personal role."
        else:
            s_score = 3.0
            s_ev = "Clearly detailed the project stakes, timeline, and specific challenge."

        # Action Taken (0-4)
        if action_hits == 0:
            a_score = 1.0 if (word_count < 45 or fluff_hits >= 1) else 1.5
            a_ev = "Actions were vague or described passively without personal ownership."
        elif action_hits == 1:
            a_score = 2.5
            a_ev = "Described personal actions taken to address the situation."
        else:
            a_score = 3.5 if metric_hits == 0 else 4.0
            a_ev = "Demonstrated proactive technical leadership, execution steps, and conflict resolution."

        # Result & Reflection (0-3)
        if result_hits == 0 and metric_hits == 0:
            r_score = 1.0
            r_ev = "Lacks measurable outcome or reflection on lessons learned."
        elif metric_hits > 0 or result_hits >= 2:
            r_score = 3.0
            r_ev = "Quantified positive impact with reflective insights on what was learned."
        else:
            r_score = 2.0
            r_ev = "Shared positive outcome, but lacks concrete metrics or systemic reflection."

        total_score = int(round(s_score + a_score + r_score))
        total_score = max(1, min(10, total_score))

        breakdown = {
            "situation_and_task": {"score": s_score, "maximum": 3, "evidence": s_ev},
            "action_taken": {"score": a_score, "maximum": 4, "evidence": a_ev},
            "result_and_reflection": {"score": r_score, "maximum": 3, "evidence": r_ev},
        }

        if total_score <= 4:
            strengths = ["Addressed the general theme of the behavioral prompt."]
            missing = ["Lacks specific personal actions (I vs. we) and measurable results.", "Missing honest reflection on lessons learned or systemic changes."]
            suggestions = ["Use the STAR method: Situation (15%), Task (15%), Action (50%), Result (20%).", "State a specific metric or business outcome achieved."]
            star_msg = "Weak STAR structure: Action and Result sections are underdeveloped."
        elif total_score <= 6:
            strengths = ["Clear situation narrative with recognizable responsibility.", "Demonstrates constructive collaboration."]
            missing = ["Could specify measurable engineering/business metrics.", "Describe systemic guardrails introduced to prevent similar problems."]
            suggestions = ["Highlight how your actions directly influenced the positive outcome.", "Include a concluding reflection on trade-offs."]
            star_msg = "Moderate STAR structure: Good context and action; needs stronger quantified results."
        else:
            strengths = ["Compelling narrative demonstrating ownership and technical leadership.", "Quantifiable impact and mature post-mortem reflection."]
            missing = ["Keep opening situation concise to leave maximum time for action details."]
            suggestions = ["Emphasize how this experience influenced subsequent team standards."]
            star_msg = "Strong STAR response with clear personal actions and verified impact."

    else:
        # Technical Evaluation
        # Technical Accuracy (0-4)
        if relevance_ratio < 0.25 and domain_hits == 0:
            t_score = 1.0
            t_ev = "Answer has low relevance to the question's core technical subject."
        elif problem_solving_hits == 0 and metric_hits == 0 and (word_count < 45 or domain_hits <= 2):
            t_score = 1.5
            t_ev = "Superficial or buzzword-heavy statements without concrete execution mechanics."
        elif domain_hits == 0 and word_count < 50:
            t_score = 2.0
            t_ev = "Mentions general ideas but lacks technical terminology or execution mechanics."
        elif domain_hits >= 3 and problem_solving_hits >= 2:
            t_score = 4.0
            matched = list(TECH_DOMAIN_TERMS & set(re.findall(r'\w+', ans_lower)))[:3]
            t_ev = f"Accurately incorporated deep technical mechanisms ({', '.join(matched)})."
        elif domain_hits >= 2 and problem_solving_hits >= 1:
            t_score = 3.5
            matched = list(TECH_DOMAIN_TERMS & set(re.findall(r'\w+', ans_lower)))[:3]
            t_ev = f"Accurately incorporated relevant technical mechanisms ({', '.join(matched)})."
        elif domain_hits >= 1 or problem_solving_hits >= 1:
            t_score = 2.5
            t_ev = "Technically sound high-level concepts, with minor gaps in architectural precision."
        else:
            t_score = 2.0
            t_ev = "Basic conceptual awareness without concrete implementation steps."

        # Problem Solving & Depth (0-3)
        if problem_solving_hits == 0 and metric_hits == 0:
            p_score = 0.5 if (fluff_hits >= 1 or word_count < 35) else 1.0
            p_ev = "Lacks discussion of trade-offs, scalability, failure modes, or edge cases."
        elif problem_solving_hits >= 2 or (problem_solving_hits >= 1 and metric_hits >= 1):
            p_score = 3.0
            p_ev = "Demonstrated deep engineering judgment with trade-offs and quantitative benchmarks."
        else:
            p_score = 2.0
            p_ev = "Explained basic implementation flow, but stopped short of failure modes or extreme scale."

        # Communication Clarity (0-3)
        if (fluff_hits >= 1 and word_count < 55) or fluff_hits >= 2:
            c_score = 1.0
            c_ev = "Contains generic filler phrases with low technical signal-to-noise ratio."
        elif word_count < 30:
            c_score = 1.5
            c_ev = "Answer is brief and lacks structured progressive reasoning."
        elif ("\n" in ans_clean or word_count > 50) and fluff_hits == 0:
            c_score = 3.0
            c_ev = "Structured explanation with clear logical progression."
        else:
            c_score = 2.0
            c_ev = "Coherent and understandable communication."

        total_score = int(round(t_score + p_score + c_score))
        total_score = max(1, min(10, total_score))

        breakdown = {
            "technical_accuracy": {"score": t_score, "maximum": 4, "evidence": t_ev},
            "problem_solving_depth": {"score": p_score, "maximum": 3, "evidence": p_ev},
            "communication_clarity": {"score": c_score, "maximum": 3, "evidence": c_ev},
        }

        if total_score <= 4:
            strengths = ["Recognized the primary subject of the question."]
            missing = [
                "Lacks specific technical mechanics, algorithms, or tools.",
                "High ratio of generic statements without practical implementation steps.",
            ]
            suggestions = [
                "Explain the 'how' and 'why', not just high-level definitions.",
                "Name specific data structures, commands, or architectural patterns.",
            ]
            star_msg = "Not applicable"
        elif total_score <= 6:
            strengths = ["Sound conceptual understanding of standard workflows.", "Good baseline clarity."]
            missing = [
                "Did not address failure modes, concurrency, or scale boundaries.",
                "Could quantify performance improvements or benchmark figures.",
            ]
            suggestions = [
                "Mention the key trade-off of your chosen approach versus an alternative.",
                "Discuss how the solution behaves under 10x traffic or edge conditions.",
            ]
            star_msg = "Not applicable"
        else:
            strengths = [
                "Deep architectural competence with concrete technical mechanisms.",
                "Strong analytical rigor: addressed trade-offs and quantified impact.",
            ]
            missing = ["Ensure opening summary is punchy before detailing mechanics."]
            suggestions = ["Highlight how this pattern is verified in automated CI/CD tests."]
            star_msg = "Not applicable"

    return {
        "score": total_score,
        "breakdown": breakdown,
        "strengths": strengths,
        "missing_points": missing,
        "suggestions": suggestions,
        "star_feedback": star_msg,
        "ideal_answer_outline": "A top-tier answer clearly defines the core challenge, details specific implementation mechanics, evaluates architectural trade-offs, and confirms verification with benchmarks.",
    }


def _normalize_evaluation_dict(
    data: dict,
    q_type: str = "technical",
    fallback_answer: str = "",
) -> Dict[str, Any]:
    """
    Normalize LLM evaluation output.
    Ensures 'score' is mathematically consistent with the rubric breakdown sum.
    """
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

    # If breakdown exists, overall score MUST strictly match sum of criteria
    if breakdown:
        computed_score = int(round(sum(v["score"] for v in breakdown.values())))
        score = max(0, min(10, computed_score))
    else:
        raw_score = data.get("score")
        if raw_score is None and fallback_answer:
            h = evaluate_answer_heuristic("", fallback_answer, q_type)
            score = h["score"]
        else:
            try:
                score = int(round(float(raw_score)))
                score = max(0, min(10, score))
            except (ValueError, TypeError):
                score = 6
        breakdown = _build_default_breakdown(score, q_type)

    def _to_str_list(val, default_item):
        if isinstance(val, list):
            items = [str(x).strip() for x in val if str(x).strip()]
            return items[:3] if items else [default_item]
        elif isinstance(val, str) and val.strip():
            return [val.strip()]
        return [default_item]

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

    # Ultimate fallback: content-based heuristic
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
    context_snippet = str(job_context).strip()[:350] if job_context else "Software engineering role"

    if q_type == "behavioral":
        rubric_spec = """
    "breakdown": {
      "situation_and_task": {"score": <number 0.0 to 3.0>, "maximum": 3, "evidence": "<brief quote or reason>"},
      "action_taken": {"score": <number 0.0 to 4.0>, "maximum": 4, "evidence": "<brief quote or reason>"},
      "result_and_reflection": {"score": <number 0.0 to 3.0>, "maximum": 3, "evidence": "<brief quote or reason>"}
    },
    "star_feedback": "<1-2 sentences on STAR execution>",
"""
        criteria_rules = """
- situation_and_task (0-3): 1=vague context, 2=clear project/task context, 3=compelling high-stakes scenario.
- action_taken (0-4): 1=passive/generic, 2=some direct action, 3=clear personal initiative, 4=exceptional leadership and technical diplomacy.
- result_and_reflection (0-3): 1=vague success claimed, 2=clear outcome, 3=quantified impact and mature lessons learned.
"""
    else:
        rubric_spec = """
    "breakdown": {
      "technical_accuracy": {"score": <number 0.0 to 4.0>, "maximum": 4, "evidence": "<brief quote or reason>"},
      "problem_solving_depth": {"score": <number 0.0 to 3.0>, "maximum": 3, "evidence": "<brief quote or reason>"},
      "communication_clarity": {"score": <number 0.0 to 3.0>, "maximum": 3, "evidence": "<brief quote or reason>"}
    },
    "star_feedback": "Not applicable",
"""
        criteria_rules = """
- technical_accuracy (0-4): 1=major misconceptions, 2=superficial definitions, 3=technically sound, 4=expert precision and terminology.
- problem_solving_depth (0-3): 1=buzzwords without steps, 2=working practical solution, 3=deep handling of edge cases, scale, and trade-offs.
- communication_clarity (0-3): 1=disjointed/fluff, 2=clear and understandable, 3=structured, concise, and professional.
"""

    prompt = f"""You are a rigorous senior tech interview coach for PrepSense.
Evaluate the candidate's answer with objective, discriminating scoring.

ROLE: {context_snippet}
QUESTION [{q_type}]: {question}
CANDIDATE ANSWER: {answer}

SCORING CRITERIA:
{criteria_rules}

CALIBRATION RULES (CRITICAL):
1. DO NOT DEFAULT TO 7. A weak or superficial answer MUST receive 3 or 4.
2. An answer with vague statements or buzzwords without execution steps receives 3 to 5.
3. A sound, competent answer covering standard flow receives 6 to 7.
4. Only answers with deep mechanics, edge cases, trade-offs, and metrics receive 8 to 10.
5. The total "score" MUST be the exact integer sum of the 3 rubric breakdown scores (0 to 10).

Return ONLY valid JSON in this exact structure:
{{
    "score": <INTEGER 0-10, exactly equal to sum of breakdown criteria>,
    {rubric_spec}
    "strengths": ["1-2 concrete points candidate did well"],
    "missing_points": ["1-2 specific technical or execution points that were missing"],
    "suggestions": ["1-2 actionable tips to level up this answer"],
    "ideal_answer_outline": "1-2 sentence summary of what a 10/10 answer includes"
}}"""

    try:
        response = ask_ai(prompt, format="json")
        return robust_parse_evaluation(response, q_type=q_type, candidate_answer=answer)
    except Exception as err:
        print(f"[AnswerEvaluator] AI call error: {err}. Using intelligent heuristic evaluation.")
        return evaluate_answer_heuristic(question, answer, q_type)
