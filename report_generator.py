"""
PrepSense - Candidate Interview Report Generator.

Generates a downloadable, print-ready HTML report (which Streamlit
serves as an in-browser download) covering:
  - Candidate profile & session metadata
  - Skill gap analysis (matched / partial / missing)
  - Answer-by-answer evaluation with rubric breakdown
  - Performance analytics (score trend, rubric averages)
  - Learning roadmap summary
  - Activity history

No third-party PDF library required: the HTML is styled with print-friendly
CSS (@media print + page-break rules) so the browser's native "Print → Save
as PDF" produces a clean multi-page PDF.  We also embed an optional
st.download_button wrapper for one-click download of the raw HTML.
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any, Dict, List, Optional


# ─── Colour palette (matches PrepSense brand) ────────────────────────────────
_PRIMARY   = "#FF5A36"
_PRIMARY_L = "#FF8A5B"
_BG        = "#FDFAF8"
_CARD_BG   = "#FFFFFF"
_BORDER    = "#E8E0D8"
_TEXT      = "#2D2520"
_MUTED     = "#7A6E68"
_GREEN     = "#22C55E"
_AMBER     = "#F59E0B"
_RED       = "#EF4444"
_BLUE      = "#3B82F6"


def _e(text: Any) -> str:
    """HTML-escape any value safely."""
    return html.escape(str(text) if text is not None else "")


def _score_color(score: float, max_score: float = 10.0) -> str:
    ratio = score / max(max_score, 1)
    if ratio >= 0.75:
        return _GREEN
    if ratio >= 0.5:
        return _AMBER
    return _RED


def _skill_badge(status: str) -> str:
    colors = {
        "matched":  (_GREEN,  "✓ Matched"),
        "partial":  (_AMBER,  "~ Partial"),
        "missing":  (_RED,    "✗ Missing"),
    }
    color, label = colors.get(status.lower(), (_BLUE, status.title()))
    return (
        f"<span style='background:{color}20;color:{color};border:1px solid {color}50;"
        f"border-radius:4px;padding:2px 7px;font-size:11px;font-weight:600'>{label}</span>"
    )


# ─── CSS ─────────────────────────────────────────────────────────────────────

_CSS = f"""
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: {_BG};
    color: {_TEXT};
    font-size: 13px;
    line-height: 1.6;
  }}

  .page {{
    max-width: 800px;
    margin: 0 auto;
    padding: 32px 24px 48px;
  }}

  /* ── Header ── */
  .report-header {{
    background: linear-gradient(135deg, {_PRIMARY}, {_PRIMARY_L});
    color: white;
    padding: 28px 32px;
    border-radius: 12px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .report-header .brand {{ font-size: 10px; letter-spacing: 2px; opacity: .75; margin-bottom: 4px; }}
  .report-header .title {{ font-size: 22px; font-weight: 700; }}
  .report-header .subtitle {{ font-size: 13px; opacity: .85; margin-top: 4px; }}
  .report-header .meta {{ text-align: right; opacity: .85; font-size: 11px; line-height: 1.8; }}

  /* ── Section ── */
  .section {{ margin-bottom: 24px; }}
  .section-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {_PRIMARY};
    padding-bottom: 6px;
    border-bottom: 2px solid {_PRIMARY};
    margin-bottom: 14px;
  }}

  /* ── Cards ── */
  .card {{
    background: {_CARD_BG};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
  }}
  .card-title {{ font-weight: 600; font-size: 13px; margin-bottom: 4px; }}
  .card-meta  {{ font-size: 11px; color: {_MUTED}; margin-bottom: 8px; }}

  /* ── Stat grid ── */
  .stat-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
  .stat-box {{
    background: {_CARD_BG};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 12px;
    text-align: center;
  }}
  .stat-label {{ font-size: 9px; letter-spacing: 1px; color: {_MUTED}; text-transform: uppercase; }}
  .stat-value {{ font-size: 20px; font-weight: 700; color: {_TEXT}; margin-top: 4px; }}

  /* ── Score badge ── */
  .score-badge {{
    display: inline-block;
    font-size: 15px;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 6px;
    color: white;
  }}

  /* ── Rubric bar ── */
  .rubric-row {{ margin: 6px 0; }}
  .rubric-label {{ font-size: 11px; color: {_MUTED}; margin-bottom: 2px; }}
  .bar-track {{
    background: {_BORDER};
    border-radius: 4px;
    height: 8px;
    width: 100%;
    overflow: hidden;
  }}
  .bar-fill {{ height: 100%; border-radius: 4px; }}

  /* ── Skill table ── */
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: {_BG}; font-size: 10px; letter-spacing: 1px; text-transform: uppercase;
        color: {_MUTED}; padding: 8px 10px; text-align: left; border-bottom: 1px solid {_BORDER}; }}
  td {{ padding: 9px 10px; border-bottom: 1px solid {_BORDER}; vertical-align: top; font-size: 12px; }}
  tr:last-child td {{ border-bottom: none; }}

  /* ── Roadmap phase ── */
  .phase-title {{
    font-weight: 700;
    color: {_PRIMARY};
    font-size: 13px;
    margin: 14px 0 6px;
  }}
  .milestone-row {{
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin: 4px 0;
    font-size: 12px;
  }}
  .milestone-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {_PRIMARY};
    margin-top: 5px;
    flex-shrink: 0;
  }}

  /* ── Activity log ── */
  .activity-row {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid {_BORDER};
    font-size: 12px;
  }}
  .activity-time {{ color: {_MUTED}; font-size: 10px; white-space: nowrap; min-width: 110px; }}

  /* ── Footer ── */
  .report-footer {{
    text-align: center;
    color: {_MUTED};
    font-size: 10px;
    letter-spacing: 1px;
    margin-top: 32px;
    border-top: 1px solid {_BORDER};
    padding-top: 16px;
  }}

  /* ── Print media ── */
  @media print {{
    body {{ background: white; }}
    .page {{ max-width: 100%; padding: 16px 20px; }}
    .card, .stat-box {{ break-inside: avoid; }}
    .section {{ break-inside: avoid; }}
    .report-header {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .score-badge {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .bar-fill   {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
</style>
"""


# ─── Section builders ─────────────────────────────────────────────────────────

def _header_html(account: Dict, result: Optional[Dict]) -> str:
    name = _e(account.get("name", "Candidate"))
    uid  = _e(account.get("id", ""))
    role = _e(account.get("target_role", "Software Engineer"))
    company = _e((result or {}).get("company_name", "—"))
    job_title = _e(((result or {}).get("job_info") or {}).get("job_title") or "—")
    generated = datetime.now().strftime("%d %b %Y, %I:%M %p")
    return f"""
<div class="report-header">
  <div>
    <div class="brand">PREPSENSE · INTERVIEW REPORT</div>
    <div class="title">{name}</div>
    <div class="subtitle">{role}  &nbsp;·&nbsp;  ID: {uid}</div>
  </div>
  <div class="meta">
    <div><strong>Target Company:</strong> {company}</div>
    <div><strong>Applied Role:</strong> {job_title}</div>
    <div style="margin-top:8px;font-size:10px">Generated: {generated}</div>
  </div>
</div>
"""


def _stats_html(account: Dict, evaluation_history: Dict, result: Optional[Dict]) -> str:
    stats = account.get("stats", {})
    total_inputs   = stats.get("total_inputs", 0)
    total_sessions = stats.get("total_interviews", 0)
    scores_hist    = stats.get("scores_history", [])
    avg_score      = round(stats.get("average_score", 0.0), 1)
    total_q        = len((result or {}).get("questions", []))

    evals = list(evaluation_history.values())
    session_avg = round(sum(e.get("score", 0) for e in evals) / max(len(evals), 1), 1) if evals else "—"

    boxes = [
        ("SESSION QUESTIONS", total_q),
        ("ANSWERS EVALUATED", len(evals)),
        ("SESSION AVG SCORE", f"{session_avg}/10" if evals else "—"),
        ("LIFETIME AVG", f"{avg_score}/10" if scores_hist else "—"),
        ("TOTAL SESSIONS", total_sessions),
        ("TOTAL ANSWERS", total_inputs),
    ]
    items = "".join(
        f"<div class='stat-box'>"
        f"<div class='stat-label'>{_e(label)}</div>"
        f"<div class='stat-value'>{_e(val)}</div>"
        f"</div>"
        for label, val in boxes
    )
    return f"<div class='stat-grid' style='grid-template-columns:repeat(3,1fr)'>{items}</div>"


def _skill_gap_html(skill_gap_report: Optional[Dict]) -> str:
    if not skill_gap_report:
        return "<p style='color:#7A6E68;font-size:12px'>No skill-gap data available for this session.</p>"

    assessments = skill_gap_report.get("skill_assessments", [])
    if not assessments:
        return "<p style='color:#7A6E68;font-size:12px'>Skill assessments not found in report.</p>"

    rows = ""
    for skill in assessments:
        name    = _e(skill.get("skill", "—"))
        status  = skill.get("status", "unknown")
        badge   = _skill_badge(status)
        reason  = _e(skill.get("explanation") or skill.get("reason") or "—")
        evidence= _e(skill.get("resume_evidence") or skill.get("evidence") or "—")
        reco    = _e(skill.get("recommendation") or "—")
        rows += f"""
<tr>
  <td style="font-weight:600">{name}</td>
  <td>{badge}</td>
  <td style="color:#2D2520">{reason}</td>
  <td style="color:#7A6E68;font-style:italic">{evidence[:120] + "…" if len(evidence) > 120 else evidence}</td>
  <td style="color:#3B82F6;font-size:11px">{reco[:80] + "…" if len(reco) > 80 else reco}</td>
</tr>"""
    return f"""
<table>
  <thead><tr>
    <th>Skill</th><th>Status</th><th>Assessment</th><th>Resume Evidence</th><th>Recommendation</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>"""


def _evaluations_html(evaluation_history: Dict, answer_feedback: Dict) -> str:
    if not evaluation_history:
        return "<p style='color:#7A6E68;font-size:12px'>No answers evaluated in this session yet.</p>"

    cards = ""
    for idx, (key, item) in enumerate(evaluation_history.items(), start=1):
        q_text  = _e(item.get("question", "—"))
        q_type  = item.get("question_type", "technical").title()
        score   = item.get("score", 0)
        s_color = _score_color(score)
        breakdown = item.get("breakdown") or answer_feedback.get(key, {}).get("breakdown", {})

        rubric_html = ""
        for crit, detail in breakdown.items():
            crit_label = crit.replace("_", " ").title()
            c_score = float(detail.get("score", 0))
            c_max   = float(detail.get("maximum", 1))
            pct     = round(100 * c_score / max(c_max, 1))
            fill_color = _score_color(c_score, c_max)
            evidence = _e(detail.get("evidence", ""))
            rubric_html += f"""
<div class="rubric-row">
  <div class="rubric-label">{_e(crit_label)} &nbsp; {c_score:.1f} / {int(c_max)}</div>
  <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{fill_color}"></div></div>
  <div style="font-size:10px;color:#7A6E68;margin-top:2px">{evidence}</div>
</div>"""

        strengths = answer_feedback.get(key, {}).get("strengths", [])
        missing   = answer_feedback.get(key, {}).get("missing_points", [])
        s_bullets = "".join(f"<li>{_e(s)}</li>" for s in strengths)
        m_bullets = "".join(f"<li>{_e(m)}</li>" for m in missing)

        cards += f"""
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div class="card-title">Q{idx}: {q_text[:120] + "…" if len(q_text) > 120 else q_text}</div>
      <div class="card-meta">Type: {_e(q_type)}</div>
    </div>
    <span class="score-badge" style="background:{s_color}">{score}/10</span>
  </div>
  {rubric_html}
  {'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px">' if s_bullets or m_bullets else ''}
  {'<div><div style="font-size:11px;font-weight:600;color:#22C55E;margin-bottom:4px">✅ Strengths</div><ul style=\'margin-left:16px;font-size:12px\'>' + s_bullets + '</ul></div>' if s_bullets else ''}
  {'<div><div style="font-size:11px;font-weight:600;color:#EF4444;margin-bottom:4px">⚠ Missing Points</div><ul style=\'margin-left:16px;font-size:12px\'>' + m_bullets + '</ul></div>' if m_bullets else ''}
  {'</div>' if s_bullets or m_bullets else ''}
</div>"""
    return cards


def _roadmap_html(roadmap: Optional[Dict]) -> str:
    if not roadmap:
        return "<p style='color:#7A6E68;font-size:12px'>No learning roadmap generated for this session.</p>"

    phases = roadmap.get("phases", [])
    if not phases:
        return "<p style='color:#7A6E68;font-size:12px'>Roadmap phases not found.</p>"

    out = ""
    for phase in phases:
        p_title = _e(phase.get("phase_name") or phase.get("title", "Phase"))
        p_goal  = _e(phase.get("goal", ""))
        out += f"<div class='phase-title'>📌 {p_title}</div>"
        if p_goal:
            out += f"<div style='font-size:11px;color:#7A6E68;margin-bottom:6px'>{p_goal}</div>"
        for ms in phase.get("milestones", []):
            ms_title = _e(ms.get("title", ms.get("name", "Milestone")))
            ms_hours = ms.get("estimated_hours", "")
            out += f"""
<div class="milestone-row">
  <div class="milestone-dot"></div>
  <div>{ms_title}{"&nbsp;&nbsp;<span style='color:#7A6E68;font-size:11px'>(" + str(ms_hours) + "h)</span>" if ms_hours else ""}</div>
</div>"""
    return out


def _activity_html(account: Dict) -> str:
    activities = account.get("recent_activity", [])
    if not activities:
        return "<p style='color:#7A6E68;font-size:12px'>No activity recorded yet.</p>"

    rows = ""
    type_icons = {
        "answer_evaluated":  "📝",
        "interview_created": "🎯",
        "skill_analysis_run":"🔍",
        "roadmap_generated": "🗺️",
        "adaptive_followup": "🧠",
        "coding_challenge":  "💻",
        "Interview Created":  "🎯",
        "Answer Evaluated":   "📝",
    }
    for act in activities[:15]:
        atype = act.get("type", act.get("action", "activity"))
        icon  = type_icons.get(atype, "📌")
        label = atype.replace("_", " ").title()
        ts    = act.get("timestamp", "")[:16].replace("T", " ")

        detail_parts = []
        if act.get("company"):   detail_parts.append(f"Company: <b>{_e(act['company'])}</b>")
        if act.get("role"):      detail_parts.append(f"Role: {_e(act['role'])}")
        if act.get("question"):  detail_parts.append(f"Q: {_e(act['question'][:70])}…")
        if act.get("score") is not None: detail_parts.append(f"Score: <b>{_e(act['score'])}/10</b>")
        if act.get("challenge"): detail_parts.append(f"Challenge: {_e(act['challenge'])}")
        if act.get("detail"):    detail_parts.append(_e(act["detail"]))

        rows += f"""
<div class="activity-row">
  <div class="activity-time">{ts}</div>
  <div>{icon} <b>{_e(label)}</b> &nbsp; {" &nbsp;·&nbsp; ".join(detail_parts)}</div>
</div>"""
    return rows


# ─── Main builder ─────────────────────────────────────────────────────────────

def build_report_html(
    account: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    skill_gap_report: Optional[Dict[str, Any]] = None,
    evaluation_history: Optional[Dict[str, Any]] = None,
    answer_feedback: Optional[Dict[str, Any]] = None,
    roadmap: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Assemble the full candidate report as a self-contained HTML string.

    Parameters
    ----------
    account            : Active account dict from account_manager.get_active_account()
    result             : st.session_state.interview_result
    skill_gap_report   : st.session_state.skill_gap_report
    evaluation_history : st.session_state.evaluation_history
    answer_feedback    : st.session_state.answer_feedback
    roadmap            : st.session_state.learning_roadmap
    """
    ev_hist = evaluation_history or {}
    ans_fb  = answer_feedback or {}

    # Score summary for skill gap stats
    assessments = (skill_gap_report or {}).get("skill_assessments", [])
    matched  = sum(1 for a in assessments if a.get("status", "").lower() == "matched")
    partial  = sum(1 for a in assessments if a.get("status", "").lower() == "partial")
    missing  = sum(1 for a in assessments if a.get("status", "").lower() == "missing")

    # Sections
    has_evals    = bool(ev_hist)
    has_skills   = bool(assessments)
    has_roadmap  = bool(roadmap and roadmap.get("phases"))
    has_activity = bool(account.get("recent_activity"))

    toc_items = ["📊 Performance Summary"]
    if has_skills:   toc_items.append("🔍 Skill Gap Analysis")
    if has_evals:    toc_items.append("🎙️ Answer Evaluations")
    if has_roadmap:  toc_items.append("🗺️ Learning Roadmap")
    if has_activity: toc_items.append("📜 Activity History")
    toc_html = " &nbsp;·&nbsp; ".join(f"<span style='font-size:11px'>{t}</span>" for t in toc_items)

    skill_summary = ""
    if has_skills:
        skill_summary = f"""
<div style='display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap'>
  <span style='background:{_GREEN}20;color:{_GREEN};border:1px solid {_GREEN}50;border-radius:4px;padding:3px 10px;font-size:12px;font-weight:600'>✓ {matched} Matched</span>
  <span style='background:{_AMBER}20;color:{_AMBER};border:1px solid {_AMBER}50;border-radius:4px;padding:3px 10px;font-size:12px;font-weight:600'>~ {partial} Partial</span>
  <span style='background:{_RED}20;color:{_RED};border:1px solid {_RED}50;border-radius:4px;padding:3px 10px;font-size:12px;font-weight:600'>✗ {missing} Missing</span>
</div>"""

    sections_html = f"""
<div class="section">
  <div class="section-title">📊 Performance Summary</div>
  {_stats_html(account, ev_hist, result)}
</div>
"""
    if has_skills:
        sections_html += f"""
<div class="section">
  <div class="section-title">🔍 Skill Gap Analysis</div>
  {skill_summary}
  {_skill_gap_html(skill_gap_report)}
</div>
"""
    if has_evals:
        sections_html += f"""
<div class="section" style="break-before:page">
  <div class="section-title">🎙️ Answer Evaluations ({len(ev_hist)} answers)</div>
  {_evaluations_html(ev_hist, ans_fb)}
</div>
"""
    if has_roadmap:
        sections_html += f"""
<div class="section">
  <div class="section-title">🗺️ Learning Roadmap</div>
  <div class="card">
    {_roadmap_html(roadmap)}
  </div>
</div>
"""
    if has_activity:
        sections_html += f"""
<div class="section">
  <div class="section-title">📜 Activity History</div>
  {_activity_html(account)}
</div>
"""

    name = _e(account.get("name", "Candidate"))
    generated = datetime.now().strftime("%d %b %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PrepSense Report — {name}</title>
  {_CSS}
</head>
<body>
<div class="page">
  {_header_html(account, result)}

  <div style="margin-bottom:20px;padding:10px 14px;background:{_CARD_BG};border:1px solid {_BORDER};border-radius:8px;font-size:12px;color:{_MUTED}">
    <strong style="color:{_TEXT}">Contents:</strong>&nbsp; {toc_html}
    <br><span style="font-size:10px">To save as PDF: open this file in a browser → File → Print → Save as PDF</span>
  </div>

  {sections_html}

  <div class="report-footer">
    PREPSENSE &nbsp;·&nbsp; AI-POWERED INTERVIEW PREPARATION &nbsp;·&nbsp; {generated}
  </div>
</div>
</body>
</html>
"""


def build_report_filename(account: Dict[str, Any], result: Optional[Dict[str, Any]] = None) -> str:
    """Generate a clean filename for the downloaded report."""
    name    = account.get("name", "candidate").replace(" ", "_").lower()
    company = ((result or {}).get("company_name") or "session").replace(" ", "_").lower()
    date    = datetime.now().strftime("%Y%m%d")
    return f"prepsense_report_{name}_{company}_{date}.html"
