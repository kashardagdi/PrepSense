"""
PrepSense - Personalized Learning Roadmap Generator.

Transforms identified skill gaps, job requirements, and target company context
into a structured, phased learning roadmap with concrete milestones, practical
project ideas, curated resources, and interview checkpoints.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from llm import ask_ai


# Default resource catalog for common tech skills
RESOURCE_CATALOG: Dict[str, Dict[str, str]] = {
    "python": {
        "title": "Python Official Documentation & Real Python",
        "url": "https://realpython.com/",
    },
    "fastapi": {
        "title": "FastAPI Official Tutorial & Architecture Guide",
        "url": "https://fastapi.tiangolo.com/tutorial/",
    },
    "docker": {
        "title": "Docker Getting Started & Containerization Guide",
        "url": "https://docs.docker.com/get-started/",
    },
    "kubernetes": {
        "title": "Kubernetes Basics & Architecture",
        "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/",
    },
    "sql": {
        "title": "SQL Practice & LeetCode SQL 50 Study Plan",
        "url": "https://leetcode.com/studyplan/top-sql-50/",
    },
    "postgresql": {
        "title": "PostgreSQL Tutorial & Query Optimization",
        "url": "https://www.postgresqltutorial.com/",
    },
    "aws": {
        "title": "AWS Skill Builder & Cloud Practitioner Essentials",
        "url": "https://aws.amazon.com/training/",
    },
    "git": {
        "title": "Pro Git Book (Free) & Git Interactive Branching",
        "url": "https://learngitbranching.js.org/",
    },
    "system design": {
        "title": "System Design Primer by Donne Martin",
        "url": "https://github.com/donnemartin/system-design-primer",
    },
    "data structures": {
        "title": "NeetCode Roadmap & DSA Core Patterns",
        "url": "https://neetcode.io/roadmap",
    },
    "algorithms": {
        "title": "NeetCode DSA Roadmap & LeetCode 75",
        "url": "https://neetcode.io/practice",
    },
    "rest api": {
        "title": "RESTful API Design Best Practices",
        "url": "https://restfulapi.net/",
    },
    "javascript": {
        "title": "JavaScript.info - The Modern JavaScript Tutorial",
        "url": "https://javascript.info/",
    },
    "react": {
        "title": "React Official Documentation & Interactive Quickstart",
        "url": "https://react.dev/learn",
    },
    "ci/cd": {
        "title": "GitHub Actions Documentation & CI/CD Pipelines",
        "url": "https://docs.github.com/en/actions",
    },
    "c++": {
        "title": "LearnCpp.com - Modern C++ Tutorial",
        "url": "https://www.learncpp.com/",
    },
    "java": {
        "title": "Dev.java - The Destination for Java Developers",
        "url": "https://dev.java/learn/",
    },
    "linux": {
        "title": "Linux Journey - Command Line & Operating System Fundamentals",
        "url": "https://linuxjourney.com/",
    },
}


def _find_resource_for_skill(skill_name: str) -> Dict[str, str]:
    """Find a curated resource for a given skill or return a smart fallback."""
    normalized = skill_name.strip().lower()
    for key, res in RESOURCE_CATALOG.items():
        if key in normalized or normalized in key:
            return res
    return {
        "title": f"Roadmap.sh & Official Guides for {skill_name}",
        "url": f"https://roadmap.sh/",
    }


def _repair_truncated_json(text: str) -> str:
    """Best-effort stack-based repair for truncated JSON outputs."""
    stack = []
    in_string = False
    escape = False

    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch in "{[":
                stack.append(ch)
            elif ch == "}":
                if stack and stack[-1] == "{":
                    stack.pop()
            elif ch == "]":
                if stack and stack[-1] == "[":
                    stack.pop()

    repaired = text.rstrip()
    if in_string:
        repaired += '"'

    while stack:
        closer = stack.pop()
        if closer == "{":
            repaired += "}"
        elif closer == "[":
            repaired += "]"

    return repaired


def _extract_json(text: str) -> Any:
    """Extract and parse JSON object from LLM response text."""
    if not text or not text.strip():
        return None

    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    candidate = match.group(1) if match else cleaned

    first_brace = candidate.find("{")
    last_brace = candidate.rfind("}")
    if first_brace != -1:
        if last_brace != -1 and last_brace > first_brace:
            candidate = candidate[first_brace : last_brace + 1]
        else:
            candidate = candidate[first_brace:]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        repaired = _repair_truncated_json(candidate)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            return None


def _build_rule_based_roadmap(
    skill_gap_report: Dict[str, Any],
    job_info: Dict[str, Any],
    company_name: str = "",
    timeline_weeks: int = 4,
) -> Dict[str, Any]:
    """
    Deterministic rule-based roadmap builder.

    Guarantees that regardless of LLM availability or network status, the candidate
    instantly receives a practical, phased roadmap with milestones, mini-projects,
    and interview verification questions based directly on their skill gaps.
    """
    role = job_info.get("role") or "Target Role"
    company = company_name.strip() or "Target Company"

    assessments = skill_gap_report.get("skill_assessments", [])
    recommendations = {
        str(r.get("skill", "")).lower(): r.get("action", "")
        for r in skill_gap_report.get("recommendations", [])
        if isinstance(r, dict)
    }

    missing_skills = [
        item for item in assessments
        if isinstance(item, dict) and item.get("status") == "missing"
    ]
    partial_skills = [
        item for item in assessments
        if isinstance(item, dict) and item.get("status") == "partial"
    ]
    matched_skills = [
        item for item in assessments
        if isinstance(item, dict) and item.get("status") == "matched"
    ]

    total_assessed = len(assessments)
    readiness_score = int(round((len(matched_skills) / max(total_assessed, 1)) * 100))

    # Phase duration labels based on timeline
    if timeline_weeks <= 2:
        phase1_dur = "Days 1-5"
        phase2_dur = "Days 6-10"
        phase3_dur = "Days 11-14"
        hrs_per_week = 16
    elif timeline_weeks <= 4:
        phase1_dur = "Week 1"
        phase2_dur = "Weeks 2-3"
        phase3_dur = "Week 4"
        hrs_per_week = 10
    else:
        phase1_dur = "Weeks 1-3"
        phase2_dur = "Weeks 4-6"
        phase3_dur = "Weeks 7-8"
        hrs_per_week = 7

    # Phase 1: High-priority Missing Foundations
    p1_milestones = []
    priority_items = missing_skills[:4] if missing_skills else partial_skills[:2]
    for idx, item in enumerate(priority_items, start=1):
        skill = item.get("skill", f"Skill {idx}")
        action = recommendations.get(skill.lower()) or item.get("recommendation") or f"Learn core fundamentals of {skill}."
        resource = _find_resource_for_skill(skill)
        p1_milestones.append({
            "id": f"p1_m{idx}",
            "skill": skill,
            "status": item.get("status", "missing"),
            "priority": "Critical" if item.get("importance") == "critical" else "High",
            "task": f"Build foundational fluency in {skill}",
            "action_item": action,
            "project_or_exercise": f"Create a working sample or tutorial repository demonstrating core {skill} concepts.",
            "resource": resource,
            "interview_check": f"Be prepared to explain the architecture and trade-offs of using {skill} in a production environment.",
        })

    # If no missing skills, add an advanced mastery milestone
    if not p1_milestones and matched_skills:
        top_matched = matched_skills[0].get("skill", "Core Skills")
        p1_milestones.append({
            "id": "p1_m1",
            "skill": top_matched,
            "status": "matched",
            "priority": "Maintenance",
            "task": f"Refine advanced concepts and optimization in {top_matched}",
            "action_item": f"Review advanced patterns, concurrency, and performance tuning in {top_matched}.",
            "project_or_exercise": f"Benchmark and profile an existing application using {top_matched}.",
            "resource": _find_resource_for_skill(top_matched),
            "interview_check": f"Describe a difficult technical challenge you solved using {top_matched}.",
        })

    # Phase 2: Practical Projects & System Integration
    p2_milestones = []
    p2_candidates = partial_skills[:4] if partial_skills else missing_skills[4:8]
    if not p2_candidates and missing_skills:
        p2_candidates = missing_skills[:2]

    for idx, item in enumerate(p2_candidates, start=1):
        skill = item.get("skill", f"Skill {idx}")
        action = recommendations.get(skill.lower()) or item.get("recommendation") or f"Build an applied project with {skill}."
        resource = _find_resource_for_skill(skill)
        p2_milestones.append({
            "id": f"p2_m{idx}",
            "skill": skill,
            "status": item.get("status", "partial"),
            "priority": "Important",
            "task": f"Bridge resume gap: demonstrate hands-on experience with {skill}",
            "action_item": action,
            "project_or_exercise": f"Build a mini end-to-end service or feature incorporating {skill} with automated unit tests.",
            "resource": resource,
            "interview_check": f"How would you troubleshoot performance bottlenecks or common failures in {skill}?",
        })

    if not p2_milestones:
        p2_milestones.append({
            "id": "p2_m1",
            "skill": "System Integration & Testing",
            "status": "partial",
            "priority": "High",
            "task": "Combine core technologies into a cohesive end-to-end portfolio project",
            "action_item": "Build and containerize a full-stack REST API service with database migrations and CI/CD.",
            "project_or_exercise": "Deploy the project to a public cloud or container registry with documentation.",
            "resource": {"title": "GitHub Actions & Docker Deployment", "url": "https://docs.docker.com/"},
            "interview_check": "Walk through your deployment architecture from git push to container run.",
        })

    # Phase 3: Interview Mastery & Target Company Preparation
    p3_milestones = [
        {
            "id": "p3_m1",
            "skill": f"{company} Cultural & Behavioral Alignment",
            "status": "target",
            "priority": "Critical",
            "task": f"Master behavioral interview scenarios tailored to {company}",
            "action_item": f"Draft 5 STAR-format stories highlighting ownership, bias for action, and technical resilience aligned with {company}'s core principles.",
            "project_or_exercise": "Record or write out answers to common behavioral questions and refine metrics/impact.",
            "resource": {"title": "STAR Method Behavioral Guide", "url": "https://www.thebalancecareers.com/what-is-the-star-interview-response-technique-2061629"},
            "interview_check": f"Tell me about a time you faced a tight deadline with incomplete requirements at {company}.",
        },
        {
            "id": "p3_m2",
            "skill": "Technical Mock Interviews & Live Coding",
            "status": "target",
            "priority": "Critical",
            "task": f"Simulate real-time interview pressure for {role}",
            "action_item": f"Complete timed mock interview rounds focusing on core algorithms, system design trade-offs, and requirement clarification.",
            "project_or_exercise": "Solve 10 role-relevant medium coding problems under 25-minute time constraints.",
            "resource": {"title": "LeetCode / NeetCode Interview Patterns", "url": "https://neetcode.io/"},
            "interview_check": "Explain the time and space complexity of your solution and discuss how you would scale it.",
        },
    ]

    total_milestones = len(p1_milestones) + len(p2_milestones) + len(p3_milestones)

    return {
        "target_role": role,
        "company_name": company,
        "timeline_weeks": timeline_weeks,
        "readiness_score": readiness_score,
        "estimated_hours_per_week": hrs_per_week,
        "total_milestones": total_milestones,
        "summary": (
            f"Tailored {timeline_weeks}-week roadmap for {role} at {company}. "
            f"Focuses on bridging {len(missing_skills)} missing and {len(partial_skills)} partial skills "
            f"through targeted milestones, portfolio project deliverables, and interview checkpoints."
        ),
        "phases": [
            {
                "phase_number": 1,
                "title": f"Phase 1: High-Priority Foundations ({phase1_dur})",
                "goal": "Rapidly close critical gaps in required technologies and core concepts.",
                "milestones": p1_milestones,
            },
            {
                "phase_number": 2,
                "title": f"Phase 2: Hands-on Projects & Applied Skills ({phase2_dur})",
                "goal": "Build portfolio evidence and deepen practical problem-solving capability.",
                "milestones": p2_milestones,
            },
            {
                "phase_number": 3,
                "title": f"Phase 3: Company Mastery & Mock Interview Polish ({phase3_dur})",
                "goal": f"Finalize interview readiness with behavioral STAR stories and mock sessions for {company}.",
                "milestones": p3_milestones,
            },
        ],
        "company_prep": {
            "company": company,
            "key_focus": f"Review {company}'s engineering culture, technology stack, and leadership expectations.",
            "advice": "Quantify past achievements with clear metrics (latency reduction, lines tested, users served).",
        },
        "quick_tips": [
            f"Commit code daily to GitHub to document hands-on practice in missing skills.",
            f"Structure every behavioral answer using Situation, Task, Action, and Result (STAR).",
            f"Review company-specific question patterns in PrepSense's 'Interview Practice' tab.",
        ],
    }


def generate_learning_roadmap(
    skill_gap_report: Dict[str, Any],
    job_info: Dict[str, Any],
    company_name: str = "",
    timeline_weeks: int = 4,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Generate a personalized, phased learning roadmap.

    Attempts to synthesize customized insights using Ollama Qwen3 with a concise
    distilled prompt, and smoothly falls back to a deterministic rule-based plan
    to guarantee reliability and speed.
    """
    if not isinstance(skill_gap_report, dict):
        skill_gap_report = {}
    if not isinstance(job_info, dict):
        job_info = {}

    role = job_info.get("role") or "Target Role"
    company = company_name.strip() or "Target Company"

    # Rule-based fallback roadmap
    fallback = _build_rule_based_roadmap(
        skill_gap_report=skill_gap_report,
        job_info=job_info,
        company_name=company,
        timeline_weeks=timeline_weeks,
    )

    if not use_llm:
        return fallback

    # Extract top gap skills (max 5) to keep prompt extremely lightweight (~250 tokens)
    assessments = skill_gap_report.get("skill_assessments", [])
    gaps = [
        item.get("skill", "")
        for item in assessments
        if isinstance(item, dict) and item.get("status") in {"missing", "partial"}
    ][:5]

    if not gaps:
        return fallback

    prompt = f"""You are a senior tech career coach. Create a concise learning roadmap JSON for a candidate preparing for:
Role: {role}
Company: {company}
Timeline: {timeline_weeks} weeks
Identified Skill Gaps: {', '.join(gaps)}

Output ONLY valid JSON with this exact schema:
{{
  "summary": "<1-2 sentence overview of the preparation strategy>",
  "phases": [
    {{
      "phase_number": 1,
      "title": "Phase 1: Core Foundations",
      "goal": "<1 sentence goal>",
      "milestones": [
        {{
          "id": "p1_m1",
          "skill": "<skill name>",
          "priority": "Critical",
          "task": "<what to study>",
          "action_item": "<specific learning task>",
          "project_or_exercise": "<mini project idea to build>",
          "interview_check": "<1 interview question to test knowledge>"
        }}
      ]
    }},
    {{
      "phase_number": 2,
      "title": "Phase 2: Hands-on Projects",
      "goal": "<1 sentence goal>",
      "milestones": [
        {{
          "id": "p2_m1",
          "skill": "<skill name>",
          "priority": "High",
          "task": "<what to build>",
          "action_item": "<specific task>",
          "project_or_exercise": "<mini project idea>",
          "interview_check": "<1 interview question>"
        }}
      ]
    }},
    {{
      "phase_number": 3,
      "title": "Phase 3: Interview Mastery",
      "goal": "<1 sentence goal>",
      "milestones": [
        {{
          "id": "p3_m1",
          "skill": "{company} Cultural & Technical Polish",
          "priority": "Critical",
          "task": "<mock interview prep>",
          "action_item": "<practice task>",
          "project_or_exercise": "<behavioral STAR prep>",
          "interview_check": "<company interview question>"
        }}
      ]
    }}
  ]
}}
Do not write markdown prose outside the JSON. Return valid JSON only."""

    try:
        raw_response = ask_ai(prompt)
        parsed = _extract_json(raw_response)
        if isinstance(parsed, dict) and parsed.get("phases"):
            # Merge parsed phases with metadata & resource links
            fallback["summary"] = parsed.get("summary") or fallback["summary"]
            parsed_phases = parsed.get("phases", [])
            merged_phases = []
            for p_idx, p in enumerate(parsed_phases, start=1):
                p_num = p.get("phase_number", p_idx)
                p_title = p.get("title", f"Phase {p_num}")
                p_goal = p.get("goal", "")
                p_milestones = []
                for m_idx, m in enumerate(p.get("milestones", []), start=1):
                    skill_name = m.get("skill", f"Skill {m_idx}")
                    p_milestones.append({
                        "id": m.get("id") or f"p{p_num}_m{m_idx}",
                        "skill": skill_name,
                        "status": "gap",
                        "priority": m.get("priority", "High"),
                        "task": m.get("task", f"Master {skill_name}"),
                        "action_item": m.get("action_item", f"Complete exercises in {skill_name}"),
                        "project_or_exercise": m.get("project_or_exercise", f"Build a prototype with {skill_name}"),
                        "resource": _find_resource_for_skill(skill_name),
                        "interview_check": m.get("interview_check", f"Explain core concepts of {skill_name}"),
                    })
                if p_milestones:
                    merged_phases.append({
                        "phase_number": p_num,
                        "title": p_title,
                        "goal": p_goal,
                        "milestones": p_milestones,
                    })

            if merged_phases:
                fallback["phases"] = merged_phases
                fallback["total_milestones"] = sum(len(p.get("milestones", [])) for p in merged_phases)
            return fallback
    except Exception as err:
        print(f"[Roadmap Generator] AI generation error: {err}. Using rule-based fallback.")

    return fallback


def roadmap_to_markdown(roadmap: Dict[str, Any]) -> str:
    """Format the roadmap as a clean, downloadable Markdown document."""
    lines = [
        f"# Personalized Learning Roadmap",
        f"**Target Role:** {roadmap.get('target_role', 'Role')}  ",
        f"**Target Company:** {roadmap.get('company_name', 'Company')}  ",
        f"**Timeline:** {roadmap.get('timeline_weeks', 4)} Weeks  ",
        f"**Readiness Score:** {roadmap.get('readiness_score', 0)}%  ",
        "",
        f"## Executive Summary",
        f"{roadmap.get('summary', '')}",
        "",
        f"---",
        "",
    ]

    for phase in roadmap.get("phases", []):
        lines.append(f"## {phase.get('title', 'Phase')}")
        lines.append(f"*{phase.get('goal', '')}*\n")
        for m in phase.get("milestones", []):
            lines.append(f"### [ ] {m.get('skill')} ({m.get('priority', 'High')} Priority)")
            lines.append(f"- **Objective:** {m.get('task', '')}")
            lines.append(f"- **Action Plan:** {m.get('action_item', '')}")
            lines.append(f"- **Hands-on Project:** {m.get('project_or_exercise', '')}")
            res = m.get("resource", {})
            if res:
                lines.append(f"- **Recommended Resource:** [{res.get('title', 'Resource')}]({res.get('url', '#')})")
            lines.append(f"- **Interview Checkpoint:** {m.get('interview_check', '')}")
            lines.append("")
        lines.append("")

    tips = roadmap.get("quick_tips", [])
    if tips:
        lines.append("## High-Yield Interview Tips")
        for tip in tips:
            lines.append(f"- {tip}")
        lines.append("")

    return "\n".join(lines)
