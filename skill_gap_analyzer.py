
import json
import re

from llm import ask_ai, extract_json_string


VALID_STATUSES = {"matched", "partial", "missing"}
VALID_CATEGORIES = {"technical", "tool"}

# Max skills to analyze per call (keeps response within token budget)
MAX_SKILLS_PER_CALL = 8


def normalize_text(text: str) -> str:
    """Normalise text for comparison."""
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def extract_required_skills(job_info: dict, max_skills: int = 8) -> list:
    """
    Extract and deduplicate required technical skills
    and tools from the parsed job description.
    Capped at max_skills to keep local inference fast.
    """

    if not isinstance(job_info, dict):
        raise TypeError("job_info must be a dictionary.")

    required_skills = []
    seen = set()

    skill_fields = [
        ("technical_skills", "technical"),
        ("tools_and_technologies", "tool"),
    ]

    for field, category in skill_fields:
        values = job_info.get(field, [])

        if isinstance(values, str):
            values = [values]

        if not isinstance(values, list):
            continue

        for value in values:
            skill = str(value).strip()

            if not skill:
                continue

            key = normalize_text(skill)

            if key not in seen:
                required_skills.append({
                    "skill": skill,
                    "category": category
                })
                seen.add(key)

    if not required_skills:
        raise ValueError(
            "No technical skills or tools found in job information."
        )

    return required_skills[:max_skills]


def _repair_truncated_json(text: str) -> dict | None:
    """
    Salvage a JSON string cut off mid-generation by finding the largest prefix
    ending at '}' that forms valid JSON once unclosed brackets are closed.
    """
    if not text:
        return None

    # Scan backwards for '}'
    for i in range(len(text) - 1, -1, -1):
        if text[i] != "}":
            continue
        prefix = text[:i + 1]
        stack = []
        in_string = False
        escape = False
        valid = True
        for ch in prefix:
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch in "{[":
                stack.append(ch)
            elif ch == "}":
                if not stack or stack[-1] != "{":
                    valid = False
                    break
                stack.pop()
            elif ch == "]":
                if not stack or stack[-1] != "[":
                    valid = False
                    break
                stack.pop()
        if not valid or in_string:
            continue
        suffix = ""
        for opener in reversed(stack):
            suffix += "}" if opener == "{" else "]"
        candidate = prefix + suffix
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    return None


def robust_parse_skill_gap(response: str) -> dict:
    if not response or not response.strip():
        raise ValueError("Skill-gap analyzer returned an empty response.")

    cleaned = extract_json_string(response)

    # Attempt 1: parse as-is
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError as error:
        print(f"\n[Skill Gap] JSON parse failed at char {error.pos}. "
              f"Response length: {len(cleaned)}. Attempting truncation repair...")

    # Attempt 2: repair truncated JSON
    repaired_dict = _repair_truncated_json(cleaned)
    if repaired_dict is not None:
        print("[Skill Gap] Truncation repair succeeded.")
        return repaired_dict

    # Attempt 3: try on raw response text
    try:
        result = json.loads(response.strip())
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Attempt 4: try repair on raw response text
    repaired_raw = _repair_truncated_json(response)
    if repaired_raw is not None:
        print("[Skill Gap] Truncation repair on raw text succeeded.")
        return repaired_raw

    raise ValueError(
        "Unable to parse skill-gap JSON response. "
        f"Response was {len(cleaned)} chars (token limit may have been hit)."
    )


def validate_skill_gap_report(
    report: dict,
    required_skills: list,
    resume_text: str
) -> dict:
    """
    Validate skill classifications, resume evidence,
    and recommendation references.
    """

    assessments = report.get("skill_assessments")

    if not isinstance(assessments, list):
        raise ValueError("skill_assessments must be a list.")

    expected = {
        normalize_text(item["skill"]): item
        for item in required_skills
    }

    validated = {}
    resume_normalized = normalize_text(resume_text)

    for item in assessments:

        if not isinstance(item, dict):
            raise ValueError("Invalid skill assessment entry.")

        skill = str(item.get("skill", "")).strip()
        category = item.get("category")
        status = item.get("status")
        evidence = item.get("resume_evidence")
        reason = str(item.get("reason", "")).strip()

        key = normalize_text(skill)

        if key not in expected:
            raise ValueError(
                f"Unexpected skill returned by LLM: {skill}"
            )

        if key in validated:
            raise ValueError(
                f"Duplicate skill assessment: {skill}"
            )

        if category != expected[key]["category"]:
            raise ValueError(
                f"Incorrect category for skill: {skill}"
            )

        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category for skill: {skill}"
            )

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status for skill: {skill}"
            )

        if not reason:
            raise ValueError(
                f"Missing explanation for skill: {skill}"
            )

        if status == "missing":
            if evidence is not None:
                raise ValueError(
                    f"Missing skill {skill} must have null evidence."
                )

        else:
            if not isinstance(evidence, str) or not evidence.strip():
                raise ValueError(
                    f"Evidence required for skill: {skill}"
                )

            if normalize_text(evidence) not in resume_normalized:
                raise ValueError(
                    f"Evidence for {skill} was not found "
                    "in the supplied resume text."
                )

        validated[key] = {
            "skill": skill,
            "category": category,
            "status": status,
            "resume_evidence": evidence,
            "reason": reason
        }

    missing_entries = set(expected) - set(validated)

    if missing_entries:
        raise ValueError(
            "LLM omitted required skills: "
            + ", ".join(
                expected[key]["skill"]
                for key in missing_entries
            )
        )

    recommendations = report.get("recommendations", [])

    if not isinstance(recommendations, list):
        raise ValueError("recommendations must be a list.")

    cleaned_recommendations = []
    recommended_skills = set()

    for recommendation in recommendations:

        if not isinstance(recommendation, dict):
            raise ValueError("Invalid recommendation entry.")

        skill = str(recommendation.get("skill") or "").strip()
        action = str(recommendation.get("action") or "").strip()

        # Skip incomplete recommendations.
        if not skill or not action:
            print(
                "[Validation] Skipping incomplete recommendation."
            )
            continue

        key = normalize_text(skill)

        if key not in validated:
            raise ValueError(
                f"Recommendation references unknown skill: {skill}"
            )

        if validated[key]["status"] == "matched":
            raise ValueError(
                f"Recommendation should not target matched skill: {skill}"
            )

        if key in recommended_skills:
            continue

        cleaned_recommendations.append({
            "skill": validated[key]["skill"],
            "action": action
        })

        recommended_skills.add(key)

    # Generate deterministic fallback recommendations
    # when Qwen omits a recommendation for a skill gap.
    for key, assessment in validated.items():

        if assessment["status"] == "matched":
            continue

        if key in recommended_skills:
            continue

        skill = assessment["skill"]

        if assessment["category"] == "technical":
            action = (
                f"Study the fundamentals of {skill} and "
                f"build a small project demonstrating its use."
            )
        else:
            action = (
                f"Practise using {skill} in a hands-on exercise "
                f"or small project."
            )

        print(
            f"[Validation] Added fallback recommendation for {skill}."
        )

        cleaned_recommendations.append({
            "skill": skill,
            "action": action
        })

    return {
        "skill_assessments": list(validated.values()),
        "recommendations": cleaned_recommendations
    }


def repair_inconsistent_missing_evidence(report: dict, resume_text: str) -> dict:
    """Resolve contradictory evidence attached to assessments marked missing."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dictionary.")

    assessments = report.get("skill_assessments")
    if not isinstance(assessments, list):
        return report

    resume_normalized = normalize_text(resume_text)
    repaired_report = dict(report)
    repaired_assessments = []

    for original_item in assessments:
        if not isinstance(original_item, dict):
            repaired_assessments.append(original_item)
            continue

        item = dict(original_item)

        if item.get("status") != "missing" or item.get("resume_evidence") is None:
            repaired_assessments.append(item)
            continue

        skill = str(item.get("skill", "")).strip()
        evidence = item.get("resume_evidence")
        evidence_is_valid = (
            isinstance(evidence, str)
            and bool(evidence.strip())
            and normalize_text(evidence) in resume_normalized
        )

        if not evidence_is_valid:
            print(
                f"[Validation] Removed unsupported evidence from missing skill: {skill}."
            )
            item["resume_evidence"] = None
            repaired_assessments.append(item)
            continue

        normalized_skill = normalize_text(skill)
        normalized_evidence = normalize_text(evidence)

        exact_skill_mentioned = bool(
            re.search(
                rf"(?<![a-z0-9]){re.escape(normalized_skill)}(?![a-z0-9])",
                normalized_evidence,
                flags=re.IGNORECASE,
            )
        )
        related_postgres_evidence = (
            normalized_skill == "postgresql"
            and bool(re.search(r"\b(?:sql|mysql)\b", normalized_evidence, re.IGNORECASE))
        )

        if exact_skill_mentioned or related_postgres_evidence:
            item["status"] = "partial"
            if related_postgres_evidence:
                explanation = (
                    "The resume shows SQL/MySQL experience, which provides "
                    "transferable database knowledge, but does not demonstrate "
                    "practical PostgreSQL experience."
                )
            else:
                explanation = (
                    "The skill is mentioned in the resume, but the supplied "
                    "evidence does not establish practical use."
                )

            existing_reason = str(item.get("reason", "")).strip()
            if explanation.casefold() not in existing_reason.casefold():
                item["reason"] = f"{existing_reason} {explanation}".strip()

            print(
                f"[Validation] Changed {skill} from missing to partial "
                "because verified related evidence was supplied."
            )
        else:
            print(
                f"[Validation] Removed unrelated evidence from missing skill: {skill}."
            )
            item["resume_evidence"] = None

        repaired_assessments.append(item)

    repaired_report["skill_assessments"] = repaired_assessments
    return repaired_report


def repair_unverified_evidence(report: dict, resume_text: str) -> dict:
    """
    Ensure every matched or partial skill assessment has evidence that
    verifiably exists in the candidate's resume.

    If the LLM returned a paraphrased phrase rather than a verbatim quote:
    1. Look for a sentence or line in the resume mentioning the skill/keywords.
       If found, replace the evidence with that exact resume line.
    2. If no matching text is found in the resume, gracefully downgrade the
       status to 'missing' with null evidence so validation passes.
    """
    if not isinstance(report, dict):
        return report

    assessments = report.get("skill_assessments")
    if not isinstance(assessments, list):
        return report

    resume_normalized = normalize_text(resume_text)
    repaired_report = dict(report)
    repaired_assessments = []

    resume_lines = [
        line.strip()
        for line in re.split(r"[\n\.\;]", resume_text)
        if len(line.strip()) > 8
    ]

    for original_item in assessments:
        if not isinstance(original_item, dict):
            repaired_assessments.append(original_item)
            continue

        item = dict(original_item)
        status = item.get("status")
        evidence = item.get("resume_evidence")
        skill = str(item.get("skill", "")).strip()

        if status in ("matched", "partial"):
            evidence_valid = (
                isinstance(evidence, str)
                and bool(evidence.strip())
                and normalize_text(evidence) in resume_normalized
            )

            if not evidence_valid:
                found_quote = None
                skill_words = [w for w in re.split(r"\W+", skill.lower()) if len(w) >= 4]

                # Priority 1: line with exact skill name
                for line in resume_lines:
                    line_norm = normalize_text(line)
                    if normalize_text(skill) in line_norm:
                        found_quote = line.strip()
                        break

                # Priority 2: line containing skill word stem
                if not found_quote and skill_words:
                    for line in resume_lines:
                        line_norm = normalize_text(line)
                        if any(w[:4] in line_norm for w in skill_words):
                            found_quote = line.strip()
                            break

                if found_quote:
                    print(
                        f"[Validation] Replaced paraphrased quote for '{skill}' "
                        f"with exact resume text: '{found_quote[:50]}...'"
                    )
                    item["resume_evidence"] = found_quote
                else:
                    print(
                        f"[Validation] No verified evidence in resume for '{skill}'. "
                        "Downgrading to missing."
                    )
                    item["status"] = "missing"
                    item["resume_evidence"] = None
                    item["reason"] = f"No evidence for {skill} found in candidate resume."

        repaired_assessments.append(item)

    repaired_report["skill_assessments"] = repaired_assessments
    return repaired_report


def repair_blank_or_omitted_assessments(
    report: dict,
    required_skills: list,
    resume_text: str
) -> dict:
    """Repair blank or omitted skill assessments with one targeted LLM call."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dictionary.")

    assessments = report.get("skill_assessments")
    if not isinstance(assessments, list):
        raise ValueError("skill_assessments must be a list.")

    expected = {
        normalize_text(item["skill"]): item
        for item in required_skills
    }

    usable_assessments = []
    covered_skills = set()

    for item in assessments:
        if not isinstance(item, dict):
            usable_assessments.append(item)
            continue

        skill = str(item.get("skill") or "").strip()
        if not skill:
            print(
                "[Validation] Discarded an assessment with a blank skill name."
            )
            continue

        usable_assessments.append(item)
        key = normalize_text(skill)
        if key in expected:
            covered_skills.add(key)

    missing_skills = [
        item for key, item in expected.items()
        if key not in covered_skills
    ]

    repaired_report = dict(report)
    if not missing_skills:
        repaired_report["skill_assessments"] = usable_assessments
        return repaired_report

    missing_context = [
        {"skill": item["skill"], "category": item["category"]}
        for item in missing_skills
    ]

    repair_prompt = f"""Assess ONLY these resume skills. Return JSON only, no explanation.

SKILLS TO ASSESS:
{json.dumps(missing_context, ensure_ascii=False)}

RESUME:
{resume_text[:2000]}

Rules: matched=practical use proven, partial=listed or related tech, missing=no evidence.
Evidence must be an exact quote from the resume. null for missing skills.

Return ONLY:
{{
  "skill_assessments": [
    {{"skill": "Name", "category": "technical or tool", "status": "matched/partial/missing", "resume_evidence": "quote or null", "reason": "explanation"}}
  ]
}}"""

    print(
        "[Validation] Reassessing omitted skills: "
        + ", ".join(item["skill"] for item in missing_skills)
    )
    try:
        repair_response = ask_ai(repair_prompt)
        repair_result = robust_parse_skill_gap(repair_response)
        repair_assessments = repair_result.get("skill_assessments")
    except Exception as err:
        print(
            f"[Validation] Repair LLM call failed ({err}). Using heuristic for omitted skills."
        )
        heuristic_res = _analyze_skills_heuristic(missing_skills, resume_text)
        repair_assessments = heuristic_res.get("skill_assessments", [])

    if not isinstance(repair_assessments, list):
        raise ValueError(
            "The skill-assessment repair response did not contain a list."
        )

    usable_repair_assessments = []
    for item in repair_assessments:
        if isinstance(item, dict) and not str(item.get("skill") or "").strip():
            print(
                "[Validation] Discarded a repair assessment with a blank skill name."
            )
            continue
        usable_repair_assessments.append(item)

    repaired_report["skill_assessments"] = (
        usable_assessments + usable_repair_assessments
    )
    return repaired_report


def _build_skill_gap_prompt(job_context: dict, resume_context: str, skills_batch: list) -> str:
    """Build a concise skill-gap prompt for a subset of skills."""
    batch_context = {
        "job_title": job_context["job_title"],
        "required_skills": skills_batch
    }
    return f"""Assess each required skill against the candidate resume. Return valid JSON only.

JOB: {json.dumps(batch_context, ensure_ascii=False)}

RESUME:
{resume_context}

RULES:
- For each skill: matched=practical use proven in project/work, partial=listed or related tech only, missing=no evidence.
- resume_evidence: exact short quote (under 10 words), or null if missing.
- reason: concise explanation (under 10 words).
- recommendations: 1-2 practical improvement actions for partial/missing skills only.

Return ONLY this JSON structure:
{{
    "skill_assessments": [
        {{"skill": "Exact Name", "category": "technical or tool", "status": "matched/partial/missing", "resume_evidence": "short quote or null", "reason": "brief reason under 10 words"}}
    ],
    "recommendations": [
        {{"skill": "Exact Name", "action": "Brief improvement action."}}
    ]
}}"""


def _analyze_skills_heuristic(required_skills: list, resume_text: str) -> dict:
    """
    Intelligent heuristic fallback for skill analysis.
    Extracts verifiable text quotes directly from resume_text.
    """
    assessments = []
    recommendations = []

    # Clean lines from resume for snippet extraction
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]

    # Practical project action words indicating applied/matched proficiency
    action_words = {
        "built", "developed", "implemented", "designed", "architected",
        "created", "deployed", "optimized", "managed", "maintained",
        "engineered", "configured", "integrated", "automated", "scaled",
        "reduced", "increased", "tested", "debugged", "refactored", "experience"
    }

    for item in required_skills:
        skill = item["skill"]
        category = item.get("category", "technical")

        pattern = re.compile(
            r"(?:\b|(?<=[\s,./\-_]))" + re.escape(skill) + r"(?:\b|(?=[\s,./\-_]))",
            re.IGNORECASE,
        )
        matching_lines = [l for l in lines if pattern.search(l)]

        if matching_lines:
            has_action = False
            best_line = matching_lines[0]
            for l in matching_lines:
                words = set(re.findall(r"\w+", l.lower()))
                if words & action_words:
                    has_action = True
                    best_line = l
                    break

            idx = best_line.lower().find(skill.lower())
            if idx != -1:
                start = max(0, idx - 30)
                end = min(len(best_line), idx + len(skill) + 40)
                evidence_quote = best_line[start:end].strip()
            else:
                evidence_quote = best_line[:80].strip()

            if has_action:
                assessments.append({
                    "skill": skill,
                    "category": category,
                    "status": "matched",
                    "resume_evidence": evidence_quote,
                    "reason": f"Demonstrated practical application of {skill} in project or work experience.",
                })
            else:
                assessments.append({
                    "skill": skill,
                    "category": category,
                    "status": "partial",
                    "resume_evidence": evidence_quote,
                    "reason": f"Listed familiarity with {skill}; practical depth should be proven in interviews.",
                })
                recommendations.append({
                    "skill": skill,
                    "action": f"Build a practical project or showcase production usage of {skill}.",
                })
        else:
            assessments.append({
                "skill": skill,
                "category": category,
                "status": "missing",
                "resume_evidence": None,
                "reason": f"No direct evidence or mention of {skill} was found in the provided resume.",
            })
            recommendations.append({
                "skill": skill,
                "action": f"Study {skill} core architecture and build a working implementation to bridge this gap.",
            })

    return {
        "skill_assessments": assessments,
        "recommendations": recommendations,
    }


def analyze_skill_gap(resume_text: str, job_info: dict) -> dict:
    """
    Compare resume evidence against job requirements
    and generate a structured skill-gap report.
    Processes skills in batches to avoid hitting the token limit.
    """

    if not isinstance(resume_text, str) or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    required_skills = extract_required_skills(job_info)

    job_context = {
        "job_title": job_info.get("job_title", ""),
        "required_skills": required_skills
    }

    # Keep the input manageable for the local model.
    resume_context = resume_text.strip()[:3000]

    print(f"\n[Skill Gap Analyzer] Analysing {len(required_skills)} skills against resume...")

    try:
        # --- Batch processing ---
        # Split into chunks of MAX_SKILLS_PER_CALL to stay within token budget
        all_assessments = []
        all_recommendations = []

        for batch_start in range(0, len(required_skills), MAX_SKILLS_PER_CALL):
            batch = required_skills[batch_start: batch_start + MAX_SKILLS_PER_CALL]
            batch_num = batch_start // MAX_SKILLS_PER_CALL + 1
            total_batches = (len(required_skills) + MAX_SKILLS_PER_CALL - 1) // MAX_SKILLS_PER_CALL

            print(f"[Skill Gap Analyzer] Batch {batch_num}/{total_batches}: {[s['skill'] for s in batch]}")

            prompt = _build_skill_gap_prompt(job_context, resume_context, batch)
            response = ask_ai(prompt)  # No format="json" — Qwen handles it via prompt

            report = robust_parse_skill_gap(response)

            batch_assessments = report.get("skill_assessments", [])
            batch_recommendations = report.get("recommendations", [])

            all_assessments.extend(batch_assessments)
            all_recommendations.extend(batch_recommendations)

        combined_report = {
            "skill_assessments": all_assessments,
            "recommendations": all_recommendations
        }

        # Qwen can occasionally return a non-null quotation while labelling a
        # skill as missing. Reconcile that contradiction conservatively.
        combined_report = repair_inconsistent_missing_evidence(combined_report, resume_text)

        # Repair any blank or omitted assessments
        combined_report = repair_blank_or_omitted_assessments(
            combined_report,
            required_skills,
            resume_context
        )

        # Apply evidence consistency repair to newly generated entries too.
        combined_report = repair_inconsistent_missing_evidence(combined_report, resume_text)

        # Repair any paraphrased or unverified quotations so validation never fails
        combined_report = repair_unverified_evidence(combined_report, resume_text)

        validated_report = validate_skill_gap_report(
            combined_report,
            required_skills,
            resume_text
        )

    except Exception as e:
        print(f"[Skill Gap Analyzer] LLM analysis unavailable ({e}). Using intelligent heuristic fallback.")
        fallback_report = _analyze_skills_heuristic(required_skills, resume_text)
        validated_report = validate_skill_gap_report(
            fallback_report,
            required_skills,
            resume_text
        )

    print(
        f"[Skill Gap Analyzer] Successfully analysed "
        f"{len(validated_report['skill_assessments'])} skills."
    )

    return validated_report
