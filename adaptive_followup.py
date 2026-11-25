"""
PrepSense - Adaptive Follow-up Question Generator.

Listens to what the candidate actually answered and generates targeted,
interviewer-grade follow-up questions that probe technical trade-offs,
failure modes, edge cases, or STAR behavioral depth.
"""

from __future__ import annotations

import json
import re
from typing import Dict, Any

from llm import ask_ai, extract_json_string


def generate_adaptive_followup(
    original_question: str,
    candidate_answer: str,
    job_context: str = "",
    question_type: str = "technical",
    company: str = "",
) -> Dict[str, Any]:
    """
    Generate an adaptive follow-up question based on the candidate's actual answer.

    Uses Qwen with a strict token budget (<300 input, <250 output) and falls back
    to an intelligent, content-aware heuristic engine when offline or sandboxed.
    """
    if not original_question or not original_question.strip():
        raise ValueError("Original question cannot be empty.")

    if not candidate_answer or not candidate_answer.strip():
        return {
            "followup_question": "Could you provide a detailed response to the question so I can probe your practical experience?",
            "probe_focus": "Initial Answer Required",
            "reasoning": "No candidate answer was submitted to analyze.",
            "suggested_approach": "Structure your answer using concrete technical decisions or the STAR framework.",
        }

    # Prompt budgeted strictly within 2048 token limit
    prompt = f"""You are a senior tech lead conducting an interview at {company or 'a top tech company'}.
Analyze the candidate's answer and generate ONE targeted follow-up question to probe depth, trade-offs, or unexplained choices.

ROLE: {job_context[:100]}
TYPE: {question_type}
QUESTION: {original_question[:250]}
CANDIDATE ANSWER: {candidate_answer[:500]}

RULES:
1. Do NOT repeat the original question.
2. Probe a specific claim, technology, edge case, or trade-off the candidate mentioned.
3. Return valid JSON only.

JSON FORMAT:
{{
  "followup_question": "One deep, targeted probing question",
  "probe_focus": "Trade-off / Failure Mode / Scale & Latency / STAR Verification",
  "reasoning": "Why an interviewer asks this based on candidate's answer",
  "suggested_approach": "Key points candidate should cover in their follow-up"
}}"""

    try:
        response = ask_ai(prompt, format="json")
        cleaned = extract_json_string(response)
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and parsed.get("followup_question"):
            return {
                "followup_question": str(parsed.get("followup_question", "")).strip(),
                "probe_focus": str(parsed.get("probe_focus", "Technical Depth")).strip(),
                "reasoning": str(parsed.get("reasoning", "Probes candidate implementation choices.")).strip(),
                "suggested_approach": str(parsed.get("suggested_approach", "Explain your trade-offs and decisions.")).strip(),
            }
    except Exception as e:
        print(f"[AdaptiveFollowup] LLM unavailable ({e}). Using intelligent heuristic engine.")

    return _generate_heuristic_followup(original_question, candidate_answer, question_type)


def _generate_heuristic_followup(
    original_question: str,
    candidate_answer: str,
    question_type: str,
) -> Dict[str, Any]:
    """
    High-fidelity rule-based heuristic that inspects candidate keywords,
    architecture patterns, and metrics to craft a context-aware follow-up question.
    """
    ans_lower = candidate_answer.lower()

    if question_type == "behavioral":
        if "conflict" in ans_lower or "disagree" in ans_lower or "team" in ans_lower:
            return {
                "followup_question": "How did you manage the interpersonal relationship after the disagreement, and what specific steps did you take to ensure alignment moving forward?",
                "probe_focus": "Conflict Resolution & Long-Term Team Dynamics",
                "reasoning": "Interviewers want to see that disagreements lead to healthy team retrospectives rather than lingering friction.",
                "suggested_approach": "Highlight empathy, data-driven compromise, and how the team agreed on working norms for subsequent sprints.",
            }
        elif "failed" in ans_lower or "mistake" in ans_lower or "bug" in ans_lower:
            return {
                "followup_question": "Looking back, what early warning signs did you miss before the failure occurred, and what automated guardrail or process change did you introduce to prevent recurrence?",
                "probe_focus": "Root Cause Analysis & Post-Mortem Action Items",
                "reasoning": "Top companies evaluate candidates on whether failures result in permanent systemic improvements.",
                "suggested_approach": "Describe post-mortem culture, Blameless reviews, and telemetry/alerts added.",
            }
        else:
            return {
                "followup_question": "Could you quantify the impact of your actions—specifically what measurable business or engineering metric improved, and what would you have done differently with 50% less time?",
                "probe_focus": "Measurable Impact & Resource Constraints",
                "reasoning": "Behavioral answers often lack quantifiable results or reflections on trade-offs under pressure.",
                "suggested_approach": "State concrete metrics (e.g., % time saved, adoption rate, p99 latency) and reflect on alternative trade-offs.",
            }

    # Technical question probes based on detected topics
    if any(k in ans_lower for k in ["redis", "cache", "caching", "memcached"]):
        return {
            "followup_question": "You mentioned introducing a cache. How do you handle cache invalidation during write-heavy bursts, and what strategy prevents cache stampede or thundering herd problems on a cold start?",
            "probe_focus": "Cache Invalidation & Thundering Herd Protection",
            "reasoning": "Adding a cache is standard, but production bugs frequently occur around stale reads, eviction policies, and stampede surges.",
            "suggested_approach": "Discuss TTL strategies, cache-aside vs. write-through, probabilistic early expiration (XFetch), and mutex locking for key recalculation.",
        }

    if any(k in ans_lower for k in ["sql", "database", "postgres", "mysql", "index", "query"]):
        return {
            "followup_question": "When table volume grows from 100K rows to 100M rows, index lookups alone might degrade. How would you plan for horizontal partitioning/sharding, and how would cross-partition queries be executed?",
            "probe_focus": "Database Scalability & Sharding Strategy",
            "reasoning": "Evaluates whether the candidate understands scaling boundaries when single-node RDBMS reaches disk and memory limits.",
            "suggested_approach": "Explain choice of shard key, consistent hashing, query routing, and eventual consistency implications.",
        }

    if any(k in ans_lower for k in ["docker", "kubernetes", "microservice", "api", "rest"]):
        return {
            "followup_question": "In a distributed microservice setup, if one downstream dependency experiences high latency or intermittent packet loss, how do you prevent cascading failure across upstream services?",
            "probe_focus": "Resilience Patterns & Circuit Breaking",
            "reasoning": "Probes practical system resilience in distributed architectures.",
            "suggested_approach": "Mention circuit breakers (e.g. Resilience4j/Envoy), exponential backoff with jitter, deadlines/timeouts, and graceful degradation.",
        }

    if any(k in ans_lower for k in ["ml", "model", "train", "dataset", "pytorch", "tensorflow"]):
        return {
            "followup_question": "How do you detect and mitigate training-serving skew and data drift once this model is deployed to live production traffic?",
            "probe_focus": "Production ML Monitoring & Drift Detection",
            "reasoning": "ML systems frequently degrade silently in production due to distribution shifts.",
            "suggested_approach": "Mention feature store consistency, Kolmogorov-Smirnov tests for distribution drift, logging feature distributions, and automated retraining triggers.",
        }

    # Default technical probe
    return {
        "followup_question": f"What was the single biggest trade-off you had to make in your approach, and under what specific scale or condition would this design fail or need to be rewritten?",
        "probe_focus": "Architectural Trade-offs & Failure Boundaries",
        "reasoning": "Senior engineers are distinguished by knowing the exact failure boundaries of the code they write.",
        "suggested_approach": "Be honest about constraints: memory consumption, network latency, concurrency bottlenecks, or maintenance complexity.",
    }
