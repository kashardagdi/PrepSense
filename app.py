import json
import time
from collections import defaultdict
import streamlit as st

from pipeline import prepare_interview, analyze_candidate_skill_gap, generate_candidate_roadmap
from answer_evaluator import evaluate_answer
from roadmap_generator import roadmap_to_markdown
from adaptive_followup import generate_adaptive_followup
from code_runner import run_coding_test_cases, review_code_solution, CODING_CHALLENGES
from report_generator import build_report_html, build_report_filename
from session_manager import (
    save_session_cache,
    load_session_cache,
    clear_session_cache,
    clear_session_state_for_switch,
    restore_session_into_state,
)
from account_manager import (
    get_active_account,
    get_all_accounts,
    switch_or_create_account,
    update_account_profile,
    record_user_answer_input,
    record_interview_created,
    record_skill_analysis_run,
    record_roadmap_generated,
    record_adaptive_followup,
    record_coding_challenge_completed,
)


# ============================================================
# 1. PAGE CONFIGURATION AND SESSION STATE
# ============================================================

st.set_page_config(
    page_title="PrepSense | AI Interview Workspace",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

NAV_ITEMS = [
    "Overview",
    "Interview Practice",
    "Performance Analytics",
    "Learning Roadmap",
    "Adaptive Follow-ups",
    "Coding Interview",
    "Interview Report",
]


def initialize_state() -> None:
    defaults = {
        "current_page": "Overview",
        "_next_page": None,
        "interview_result": None,
        "interview_id": 0,
        "answer_feedback": {},
        "evaluation_history": {},
        "last_evaluated_question_index": None,
        "skill_gap_report": None,
        "skill_gap_error": None,
        "roadmap_completed": set(),
        "learning_roadmap": None,
        "nav_history": [],
        "adaptive_followups": {},
        "coding_sessions": {},
        "all_attempts_history": {},
        "coding_test_results": {},
        "coding_reviews": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Automatically restore active session from persistent cache if available
    if st.session_state.interview_result is None:
        try:
            active = get_active_account()
            active_uid = active.get("id") if active else None
        except Exception:
            active_uid = None
        restore_session_into_state(st.session_state, user_id=active_uid)


initialize_state()

# Sync with browser URL query parameters (supports native browser Back / Forward buttons)
query_page = st.query_params.get("page")
if query_page in NAV_ITEMS and query_page != st.session_state.current_page:
    st.session_state.current_page = query_page

# Apply programmatic navigation requests (e.g. from buttons or go_back)
requested_page = st.session_state.pop("_next_page", None)
if requested_page in NAV_ITEMS:
    if requested_page != st.session_state.current_page:
        history = st.session_state.setdefault("nav_history", [])
        if not history or history[-1] != st.session_state.current_page:
            history.append(st.session_state.current_page)
    st.session_state.current_page = requested_page

if st.session_state.current_page not in NAV_ITEMS:
    st.session_state.current_page = "Overview"

# Keep browser URL query param in sync with current page
st.query_params["page"] = st.session_state.current_page


# ============================================================
# 2. GLOBAL STYLING
# ============================================================

st.markdown(
    """
    <style>
    :root {
        --ps-bg: #FFF8F0;
        --ps-card: #FFFFFF;
        --ps-card-soft: #FFFDF9;
        --ps-border: #F0DFCB;
        --ps-orange: #FF5A36;
        --ps-orange-soft: #FF8A5B;
        --ps-navy: #1F2A44;
        --ps-navy-soft: #2C3A5E;
        --ps-muted: #64708A;
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 0%, rgba(255,138,91,.17), transparent 30%),
            radial-gradient(circle at 95% 90%, rgba(31,42,68,.05), transparent 32%),
            var(--ps-bg);
        color: var(--ps-navy);
    }

    .block-container {
        max-width: 1320px;
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
    }

    [data-testid="stHeader"] { background: transparent; }

    h1, h2, h3, h4 { color: var(--ps-navy) !important; letter-spacing: -.45px; }
    p, label, .stCaption { color: var(--ps-muted); }

    [data-testid="stSidebar"] {
        background: #FFFCF7;
        border-right: 1px solid var(--ps-border);
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border-radius: 10px;
        padding: 5px 8px;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(255,90,54,.07);
    }

    .ps-brand {
        display: flex;
        align-items: center;
        gap: 11px;
        padding: 8px 4px 18px 4px;
        border-bottom: 1px solid var(--ps-border);
        margin-bottom: 18px;
    }

    .ps-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 13px;
        color: white;
        font-size: 20px;
        font-weight: 900;
        background: linear-gradient(135deg, var(--ps-orange), var(--ps-orange-soft));
        box-shadow: 0 7px 18px rgba(255,90,54,.23);
    }

    .ps-brand-name { color: var(--ps-navy); font-size: 19px; font-weight: 850; letter-spacing: 1px; }
    .ps-brand-sub { color: var(--ps-muted); font-size: 10px; letter-spacing: 1.1px; }

    .ps-hero {
        background: linear-gradient(115deg, #1F2A44, #354569);
        border-radius: 23px;
        padding: 32px 34px;
        border-bottom: 4px solid var(--ps-orange);
        color: #fff;
        box-shadow: 0 14px 32px rgba(31,42,68,.14);
        margin-bottom: 22px;
    }

    .ps-hero-kicker { color: #FFAC8C; text-transform: uppercase; font-size: 10px; font-weight: 800; letter-spacing: 2px; }
    .ps-hero-title { color: #FFF8F0; font-size: clamp(26px, 3vw, 39px); font-weight: 850; line-height: 1.16; margin: 11px 0 10px 0; }
    .ps-hero-copy { color: #D5DCEC; max-width: 720px; font-size: 14px; line-height: 1.7; }

    .ps-section-kicker {
        color: var(--ps-orange);
        text-transform: uppercase;
        font-size: 10px;
        letter-spacing: 1.8px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .ps-card {
        background: var(--ps-card);
        border: 1px solid var(--ps-border);
        border-radius: 17px;
        padding: 19px 20px;
        box-shadow: 0 6px 20px rgba(31,42,68,.045);
        min-height: 120px;
    }

    .ps-card-title { color: var(--ps-navy); font-size: 15px; font-weight: 750; margin-bottom: 6px; }
    .ps-card-copy { color: var(--ps-muted); font-size: 12px; line-height: 1.6; }
    .ps-card-icon { color: var(--ps-orange); font-size: 21px; margin-bottom: 10px; }

    .ps-stat {
        background: #fff;
        border: 1px solid var(--ps-border);
        border-radius: 15px;
        padding: 16px 17px;
        box-shadow: 0 5px 18px rgba(31,42,68,.04);
    }

    .ps-stat-label { color: var(--ps-muted); font-size: 11px; font-weight: 650; }
    .ps-stat-value { color: var(--ps-navy); font-size: 27px; font-weight: 850; margin-top: 3px; }

    [data-testid="stForm"] {
        background: white;
        border: 1px solid var(--ps-border);
        border-radius: 17px;
        padding: 20px;
    }

    /* Keep input surfaces and their text readable in both Streamlit themes. */
    .stTextInput input,
    .stTextArea textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea,
    .stSelectbox [data-baseweb="select"] > div {
        background: #FFFDF9 !important;
        color: var(--ps-navy) !important;
        -webkit-text-fill-color: var(--ps-navy) !important;
        border: 1px solid var(--ps-border) !important;
        border-radius: 10px !important;
        opacity: 1 !important;
    }

    /* Placeholder text should remain visible on the light input surface. */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="textarea"] textarea::placeholder {
        color: #7C879D !important;
        -webkit-text-fill-color: #7C879D !important;
        opacity: 1 !important;
    }

    /* Labels and selected values inside Streamlit form controls. */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stFileUploader label,
    [data-testid="stWidgetLabel"] p {
        color: var(--ps-navy) !important;
    }

    .stSelectbox [data-baseweb="select"] *,
    [data-baseweb="popover"] [role="option"] {
        color: var(--ps-navy) !important;
    }

    /* File uploader: override the dark default dropzone from dark themes. */
    [data-testid="stFileUploaderDropzone"] {
        background: #FFFDF9 !important;
        border: 1px dashed #E2C7A8 !important;
        border-radius: 12px !important;
    }

    [data-testid="stFileUploaderDropzone"] *,
    [data-testid="stFileUploaderDropzoneInstructions"] {
        color: var(--ps-navy) !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: var(--ps-navy) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
    }

    [data-testid="stFileUploaderDropzone"] button * {
        color: #FFFFFF !important;
    }

    .stButton > button, .stFormSubmitButton > button {
        border-radius: 10px;
        font-weight: 700;
        min-height: 42px;
        border-color: var(--ps-border);
    }

    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(100deg, var(--ps-orange), var(--ps-orange-soft));
        color: white;
        border: none;
        box-shadow: 0 6px 16px rgba(255,90,54,.19);
    }

    [data-testid="stExpander"] {
        background: white;
        border: 1px solid var(--ps-border);
        border-radius: 12px;
        margin-bottom: 10px;
    }

    [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--ps-border);
        padding: 13px 14px;
        border-radius: 13px;
    }

    .ps-footer {
        margin-top: 42px;
        padding-top: 19px;
        border-top: 1px solid var(--ps-border);
        color: #8991A2;
        font-size: 11px;
        text-align: center;
    }

    .ps-coming-soon {
        display: inline-block;
        background: rgba(255,90,54,.09);
        color: #D94D2D;
        border: 1px solid rgba(255,90,54,.22);
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: .6px;
        text-transform: uppercase;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. COMMON HELPERS
# ============================================================


def navigate_to(page_name: str) -> None:
    if page_name in NAV_ITEMS:
        current = st.session_state.get("current_page", "Overview")
        history = st.session_state.setdefault("nav_history", [])
        if current != page_name and (not history or history[-1] != current):
            history.append(current)
        st.session_state["_next_page"] = page_name
        st.query_params["page"] = page_name
        save_session_cache(st.session_state)
        st.rerun()


def go_back() -> None:
    history = st.session_state.setdefault("nav_history", [])
    if history:
        prev_page = history.pop()
        st.session_state["_next_page"] = prev_page
        st.query_params["page"] = prev_page
        save_session_cache(st.session_state)
        st.rerun()
    else:
        navigate_to("Overview")


def render_page_header(kicker: str, title: str, description: str, show_back: bool = True) -> None:
    current_page = st.session_state.get("current_page", "Overview")
    history = st.session_state.get("nav_history", [])
    if show_back and current_page != "Overview":
        prev_label = history[-1] if history else "Overview"
        back_col, _ = st.columns([1.5, 4])
        with back_col:
            if st.button(f"← Back to {prev_label}", key=f"nav_back_{current_page}"):
                go_back()
    st.markdown(f'<div class="ps-section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)


def render_stat(label: str, value: str | int) -> None:
    st.markdown(
        f'<div class="ps-stat"><div class="ps-stat-label">{label}</div>'
        f'<div class="ps-stat-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def render_answer_feedback(feedback: dict) -> None:
    """Render the validated Version 3 rubric score, criteria breakdown and evidence."""
    score = feedback.get("score", 0)
    st.markdown("#### Your evaluation")
    score_col, status_col = st.columns([1, 2])

    with score_col:
        st.metric("Overall score", f"{score}/10")
    with status_col:
        if score >= 8:
            st.success("Strong answer — demonstrated clear competency and evidence.")
        elif score >= 6:
            st.info("Good foundation — solid approach, but key details or trade-offs can be strengthened.")
        elif score >= 4:
            st.warning("Developing answer — some relevant knowledge, but lacks technical/STAR depth.")
        else:
            st.error("Needs improvement — answer does not yet provide sufficient concrete evidence.")

    breakdown = feedback.get("breakdown", {})
    if breakdown:
        st.markdown("**Scoring breakdown by rubric criterion**")
        for criterion, details in breakdown.items():
            criterion_label = criterion.replace("_", " ").title()
            earned = details.get("score", 0)
            maximum = details.get("maximum", 0)
            label_col, mark_col = st.columns([4, 1])
            with label_col:
                st.write(f"**{criterion_label}**")
            with mark_col:
                st.write(f"**{earned}/{maximum}**")
            st.progress(min(max(earned / maximum if maximum else 0.0, 0.0), 1.0))
            evidence = details.get("evidence", "")
            if evidence:
                st.caption(f"Evidence: *{evidence}*")

    for field, heading, empty_text in [
        ("strengths", "What you did well", "No specific strengths were identified."),
        ("missing_points", "What was missing", "No major missing points were identified."),
        ("suggestions", "How to improve", "No additional suggestions were provided."),
    ]:
        st.markdown(f"**{heading}**")
        values = feedback.get(field, [])
        if values:
            for value in values:
                st.markdown(f"- {value}")
        else:
            st.caption(empty_text)

    star_feedback = feedback.get("star_feedback", "Not applicable")
    if star_feedback and star_feedback != "Not applicable":
        st.markdown("**STAR feedback**")
        st.info(star_feedback)

    ideal = feedback.get("ideal_answer_outline")
    if ideal:
        with st.expander("💡 Model Answer Blueprint (What a 10/10 Answer Includes)"):
            st.markdown(f"*{ideal}*")


def get_skill_gap_counts(report: dict) -> tuple[list, int, int, int]:
    assessments = report.get("skill_assessments", []) if isinstance(report, dict) else []
    if not isinstance(assessments, list):
        assessments = []
    matched = sum(isinstance(item, dict) and item.get("status") == "matched" for item in assessments)
    partial = sum(isinstance(item, dict) and item.get("status") == "partial" for item in assessments)
    missing = sum(isinstance(item, dict) and item.get("status") == "missing" for item in assessments)
    return assessments, matched, partial, missing


def render_skill_gap_report(report: dict) -> None:
    assessments, matched, partial, missing = get_skill_gap_counts(report)
    recommendations = report.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []
    total = matched + partial + missing

    # High-precision weighted match score (100% for full match, 50% for partial transferable knowledge)
    match_pct = round(((matched * 1.0 + partial * 0.5) / max(total, 1)) * 100, 1)

    st.markdown("#### High-Precision Skill Match Overview")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Skills Assessed", total)
    metric_cols[1].metric("Fully Matched", matched)
    metric_cols[2].metric("Partially Matched", partial)
    metric_cols[3].metric("Missing Gaps", missing)

    if total:
        st.progress(match_pct / 100.0, text=f"Overall Role Alignment: {match_pct}% (Weighted Match)")
        if match_pct >= 75:
            st.success(f"🎯 **Strong Candidate Alignment ({match_pct}% Match):** Resume provides robust evidence for core requirements.")
        elif match_pct >= 50:
            st.info(f"🟡 **Moderate Candidate Alignment ({match_pct}% Match):** Good technical foundation, with critical gaps to bridge before interview.")
        else:
            st.warning(f"⚠️ **Substantial Skill Gaps ({match_pct}% Match):** Key required technologies lack evidence on resume.")

    st.markdown("#### Skill-by-skill precision breakdown")
    labels = {
        "matched": ("✅ Matched", "Applied in projects", "#2e7d32"),
        "partial": ("🟡 Partially matched", "Conceptual / Listed", "#ed6c02"),
        "missing": ("🔴 Missing gap", "No evidence on resume", "#d32f2f"),
    }

    if not assessments:
        st.info("The report does not contain individual skill assessments.")

    for index, item in enumerate(assessments, start=1):
        if not isinstance(item, dict):
            continue
        skill = item.get("skill", f"Skill {index}")
        status = item.get("status", "unknown")
        reason = item.get("reason", "No explanation was supplied.")
        evidence = item.get("resume_evidence")
        category = str(item.get("category", "technical")).title()

        status_label, prof_level, badge_color = labels.get(status, ("Gap", "Unknown", "#757575"))

        with st.expander(f"{status_label} · {skill} ({prof_level})", expanded=status in {"partial", "missing"}):
            c_tag, c_prof = st.columns([1, 1])
            with c_tag:
                st.caption(f"Category: **{category}**")
            with c_prof:
                st.caption(f"Proficiency Assessment: **{prof_level}**")

            st.write(f"**Analysis:** {reason}")

            if evidence:
                st.markdown("**Exact verified quote from your resume:**")
                st.info(f'"{evidence}"')
            elif status == "missing":
                st.caption("No supporting keywords or project evidence were detected in the extracted resume.")

    st.markdown("#### 📚 Recommended action plan")
    if recommendations:
        for index, item in enumerate(recommendations, start=1):
            if isinstance(item, dict):
                skill = item.get("skill", f"Recommendation {index}")
                action = item.get("action") or item.get("recommendation") or item.get("suggestion")
                with st.container(border=True):
                    st.markdown(f"**{skill}**")
                    if action:
                        st.write(action)
                    else:
                        st.json(item)
    else:
        st.info("No recommendations were returned for this report.")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("🗺️ Build Phased Learning Roadmap for these Gaps →", type="primary", use_container_width=True):
        navigate_to("Learning Roadmap")


def get_current_evaluations() -> list[dict]:
    history = st.session_state.get("evaluation_history", {})
    if not isinstance(history, dict):
        return []
    current_prefix = f"{st.session_state.get('interview_id', 0)}_"
    return [value for key, value in history.items() if key.startswith(current_prefix)]


def render_footer() -> None:
    st.markdown(
        '<div class="ps-footer">PREPSENSE · COMPANY-AWARE INTERVIEW PREPARATION<br><br>'
        'Built with Python, Streamlit, LangGraph and <b>Qwen3</b></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 4. SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div class="ps-brand">
            <div class="ps-logo">P</div>
            <div><div class="ps-brand-name">PREPSENSE</div>
            <div class="ps-brand-sub">AI INTERVIEW WORKSPACE</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "account_banner" in st.session_state:
        st.success(st.session_state.pop("account_banner"))

    active_account = get_active_account()
    acc_stats = active_account.get("stats", {})
    curr_id = active_account.get("id", "default_candidate")

    with st.container(border=True):
        acc_col1, acc_col2 = st.columns([1, 2.5])
        with acc_col1:
            initial = (active_account.get("name") or "C")[:1].upper()
            st.markdown(
                f"<div style='background:linear-gradient(135deg, #FF5A36, #FF8A5B); color:white; font-size:18px; font-weight:700; border-radius:50%; width:38px; height:38px; display:flex; align-items:center; justify-content:center; margin-top:4px;'>"
                f"{initial}</div>",
                unsafe_allow_html=True,
            )
        with acc_col2:
            st.markdown(f"**{active_account.get('name', 'Candidate')}**")
            st.caption(f"{active_account.get('target_role', 'Engineer')}")

        st.caption(f"📝 **{acc_stats.get('total_inputs', 0)}** answers evaluated")
        st.caption(f"🎯 **{acc_stats.get('total_interviews', 0)}** interviews prepared")
        if acc_stats.get("scores_history"):
            st.caption(f"⭐ **{acc_stats.get('average_score', 0.0)}/10** avg score")

        with st.expander("👤 Account Switch & Settings"):
            all_accounts = get_all_accounts()
            account_keys = list(all_accounts.keys())

            tab_switch, tab_new, tab_edit = st.tabs(["🔄 Switch", "➕ New", "✏️ Edit"])

            with tab_switch:
                if len(account_keys) > 1:
                    def _format_acc(aid: str) -> str:
                        acc = all_accounts.get(aid, {})
                        aname = acc.get("name", aid.capitalize())
                        inputs = acc.get("stats", {}).get("total_inputs", 0)
                        return f"{aid} ({aname} · {inputs} inputs)"

                    curr_idx = account_keys.index(curr_id) if curr_id in account_keys else 0
                    chosen_id = st.selectbox(
                        "Registered Profiles",
                        options=account_keys,
                        index=curr_idx,
                        format_func=_format_acc,
                        key="sidebar_acc_dropdown",
                    )
                    if st.button("Switch Account →", type="primary", use_container_width=True, key="btn_switch_acc"):
                        if chosen_id != curr_id:
                            # 1. Save outgoing session
                            save_session_cache(st.session_state, user_id=curr_id)
                            # 2. Switch active user
                            switch_or_create_account(chosen_id)
                            # 3. Swap in-memory session state
                            clear_session_state_for_switch(st.session_state)
                            restore_session_into_state(st.session_state, user_id=chosen_id)
                            target_name = all_accounts.get(chosen_id, {}).get("name", chosen_id)
                            st.session_state["account_banner"] = f"✅ Switched to **{target_name}** (`{chosen_id}`). Workspace loaded!"
                            st.rerun()
                        else:
                            st.info("Already active on this account.")
                else:
                    st.caption("Only 1 account exists. Use '➕ New' tab to register another candidate profile.")

            with tab_new:
                with st.form("create_new_account_form", clear_on_submit=True):
                    new_id_input = st.text_input("Username / ID", placeholder="e.g. alex_dev", key="new_acc_id_input")
                    new_name_input = st.text_input("Candidate Name", placeholder="e.g. Alex Rivera", key="new_acc_name_input")
                    new_role_input = st.text_input("Target Role", placeholder="e.g. Backend Software Engineer", key="new_acc_role_input")
                    if st.form_submit_button("Create & Switch →", type="primary", use_container_width=True):
                        clean_new_id = new_id_input.strip().lower().replace(" ", "_")
                        if not clean_new_id:
                            st.warning("Please provide a valid Username / ID.")
                        else:
                            save_session_cache(st.session_state, user_id=curr_id)
                            switch_or_create_account(
                                user_id=clean_new_id,
                                name=new_name_input.strip(),
                                target_role=new_role_input.strip(),
                            )
                            clear_session_state_for_switch(st.session_state)
                            display_name = new_name_input.strip() or clean_new_id.capitalize()
                            st.session_state["account_banner"] = f"🎉 New profile **{display_name}** created and active!"
                            st.rerun()

            with tab_edit:
                with st.form("edit_profile_form", clear_on_submit=False):
                    edit_name = st.text_input("Candidate Name", value=active_account.get("name", ""), key="edit_name_input")
                    edit_role = st.text_input("Target Role", value=active_account.get("target_role", ""), key="edit_role_input")
                    if st.form_submit_button("Save Profile Changes", use_container_width=True):
                        update_account_profile(curr_id, name=edit_name.strip(), target_role=edit_role.strip())
                        st.session_state["account_banner"] = f"💾 Profile updated for **{curr_id}**."
                        st.rerun()

    st.caption("YOUR WORKSPACE")
    if "sidebar_nav_radio" in st.session_state and st.session_state.sidebar_nav_radio != st.session_state.current_page:
        st.session_state.sidebar_nav_radio = st.session_state.current_page

    selected_page = st.radio(
        "Navigate",
        NAV_ITEMS,
        index=NAV_ITEMS.index(st.session_state.current_page) if st.session_state.current_page in NAV_ITEMS else 0,
        key="sidebar_nav_radio",
        label_visibility="collapsed",
    )
    if selected_page != st.session_state.current_page:
        history = st.session_state.setdefault("nav_history", [])
        if not history or history[-1] != st.session_state.current_page:
            history.append(st.session_state.current_page)
        st.session_state.current_page = selected_page
        st.query_params["page"] = selected_page
        save_session_cache(st.session_state)
        st.rerun()

    st.divider()
    if st.session_state.interview_result:
        st.success("Interview session active")
        company = st.session_state.interview_result.get("company_name", "Current session")
        role = (st.session_state.interview_result.get("job_info") or {}).get("role") or ""
        st.caption(f"**{company}** {f'· {role}' if role else ''}")
        if st.button("🗑️ Reset & Start Fresh", key="sidebar_reset_btn", help="Clears this session so you can start a new interview."):
            clear_session_cache()
            for key in ["interview_result", "skill_gap_report", "skill_gap_error", "learning_roadmap"]:
                st.session_state[key] = None
            st.session_state["answer_feedback"] = {}
            st.session_state["evaluation_history"] = {}
            st.session_state["roadmap_completed"] = set()
            st.session_state["interview_id"] += 1
            st.session_state["nav_history"] = []
            st.session_state["current_page"] = "Overview"
            st.query_params["page"] = "Overview"
            st.rerun()
    else:
        st.info("No active interview session")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.caption("PrepSense · Build confidence through practice")


# ============================================================
# 5. PAGE: OVERVIEW
# ============================================================

if selected_page == "Overview":
    st.markdown(
        """
        <div class="ps-hero">
            <div class="ps-hero-kicker">Your next interview starts here</div>
            <div class="ps-hero-title">Prepare smarter.<br>Interview stronger.</div>
            <div class="ps-hero-copy">One workspace for company-aware interview preparation,
            skill-gap discovery, answer feedback and your next learning steps.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    result = st.session_state.interview_result
    active_account = get_active_account()
    acc_stats = active_account.get("stats", {})

    with st.container(border=True):
        p_col1, p_col2, p_col3, p_col4 = st.columns([1.5, 1, 1, 1])
        with p_col1:
            st.markdown(f"### 👤 {active_account.get('name', 'Candidate')}")
            st.caption(f"Profile: **{active_account.get('target_role', 'Software Engineer')}**")
        with p_col2:
            render_stat("TOTAL INPUTS", acc_stats.get("total_inputs", 0))
        with p_col3:
            render_stat("TOTAL INTERVIEWS", acc_stats.get("total_interviews", 0))
        with p_col4:
            render_stat("LIFETIME AVG", f"{acc_stats.get('average_score', 0.0)}/10" if acc_stats.get("scores_history") else "—")

    rep_btn_col1, rep_btn_col2 = st.columns([2.5, 1.5])
    with rep_btn_col2:
        if st.button("📄 Generate & Export PDF Report →", key="overview_export_report_btn", use_container_width=True):
            navigate_to("Interview Report")

    evaluations = get_current_evaluations()
    total_questions = len(result.get("questions", [])) if result else 0
    evaluated_count = len(evaluations)
    average_score = (
        sum(float(item.get("score", 0)) for item in evaluations) / evaluated_count
        if evaluated_count else 0
    )
    skill_report = st.session_state.skill_gap_report
    _, matched_count, partial_count, missing_count = get_skill_gap_counts(skill_report or {})

    metrics = st.columns(4)
    with metrics[0]:
        render_stat("INTERVIEW QUESTIONS", total_questions if result else "—")
    with metrics[1]:
        render_stat(
            "ANSWERS EVALUATED",
            f"{evaluated_count} (Session)" if result else f"{acc_stats.get('total_inputs', 0)} (Total)",
        )
    with metrics[2]:
        render_stat(
            "AVERAGE ANSWER SCORE",
            f"{average_score:.1f}/10" if evaluated_count else (f"{acc_stats.get('average_score', 0.0)}/10" if acc_stats.get('scores_history') else "—"),
        )
    with metrics[3]:
        render_stat("SKILLS FULLY MATCHED", matched_count if skill_report else "—")

    st.markdown("### Pick up where you left off")
    action_cols = st.columns(2)
    with action_cols[0]:
        with st.container(border=True):
            st.markdown("#### 🎯 Interview practice")
            st.caption("Create a company-aware interview session and practise technical and behavioral questions.")
            if st.button("Open interview practice →", key="overview_interview", type="primary", use_container_width=True):
                navigate_to("Interview Practice")
    with action_cols[1]:
        with st.container(border=True):
            st.markdown("#### 🗺️ Learning roadmap")
            st.caption("Turn identified skill gaps and role requirements into a structured, phased preparation path.")
            if st.button("Open learning roadmap →", key="overview_roadmap", use_container_width=True):
                navigate_to("Learning Roadmap")

    st.markdown("### Your preparation toolkit")
    feature_data = [
        ("📊", "Performance analytics", "Track answer scores, rubric strengths and areas to improve.", "Performance Analytics", "Available"),
        ("🗺️", "Learning roadmap", "Turn identified skill gaps into a structured, phased preparation path.", "Learning Roadmap", "Available"),
        ("🧠", "Adaptive follow-ups", "Practise deeper follow-up questions tailored to what you answered.", "Adaptive Follow-ups", "Available"),
        ("💻", "Coding interview", "Solve algorithmic challenges with real test cases and AI code reviews.", "Coding Interview", "Available"),
        ("📄", "Interview report", "Download a full PDF-ready report: scores, skill gaps, roadmap and activity history.", "Interview Report", "Available"),
    ]
    feature_cols = st.columns(2)
    for index, (icon, title, copy, destination, status) in enumerate(feature_data):
        with feature_cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"### {icon} {title}")
                st.caption(copy)
                st.caption(status)
                if st.button("Explore", key=f"overview_feature_{index}", use_container_width=True):
                    navigate_to(destination)

    if not result:
        st.info("Start by creating an interview session. Your questions, resume analysis and practice results will appear across this workspace.")
    else:
        st.success(f"Your current preparation session is for **{result.get('company_name', 'your target company')}**.")


# ============================================================
# 6. PAGE: INTERVIEW PRACTICE
# ============================================================

elif selected_page == "Interview Practice":
    render_page_header(
        "01 / PREPARE AND PRACTISE",
        "Interview Practice",
        "Build a personalized interview session, then practise each question with evidence-based AI feedback.",
    )

    result = st.session_state.interview_result

    # If an interview session is already active, present it clearly at the top
    if result:
        questions = result.get("questions", [])
        technical_count = sum(q.get("type", "").lower() == "technical" for q in questions)
        behavioral_count = sum(q.get("type", "").lower() == "behavioral" for q in questions)
        role_name = (result.get("job_info") or {}).get("role") or (result.get("job_info") or {}).get("job_title") or "Target Role"

        with st.container(border=True):
            s_col1, s_col2, s_col3 = st.columns([2, 1, 1])
            with s_col1:
                st.markdown(f"### 🎯 Active Session · {result.get('company_name', '')}")
                st.caption(f"Role: **{role_name}** · {len(questions)} Personalized Questions Ready")
            with s_col2:
                render_stat("TECHNICAL", technical_count)
            with s_col3:
                render_stat("BEHAVIORAL", behavioral_count)

            shortcut_cols = st.columns(3)
            with shortcut_cols[0]:
                if st.button("🗺️ Open Learning Roadmap →", use_container_width=True):
                    navigate_to("Learning Roadmap")
            with shortcut_cols[1]:
                if st.button("📊 Open Performance Analytics →", use_container_width=True):
                    navigate_to("Performance Analytics")
            with shortcut_cols[2]:
                if st.button("🧠 Adaptive Follow-ups →", use_container_width=True):
                    navigate_to("Adaptive Follow-ups")

    # Form to configure or start a new session (collapsed if a session is already active)
    with st.expander("➕ Configure or start a new interview session", expanded=(result is None)):
        st.markdown("### Build your interview brief")
        st.caption("Enter details below to generate a new interview session (replaces current session).")
        with st.form("interview_setup_form", clear_on_submit=False):
            company_name = st.text_input(
                "Target company",
                placeholder="e.g. Microsoft, Google, Amazon",
                key="setup_company_name",
            )
            job_description = st.text_area(
                "Job description",
                placeholder="Paste the complete job description, including skills, responsibilities and qualifications...",
                height=210,
                key="setup_job_description",
            )
            resume_pdf = st.file_uploader(
                "Your resume (PDF)",
                type=["pdf"],
                help="Upload a text-based PDF resume.",
                key="setup_resume_pdf",
            )
            submitted = st.form_submit_button(
                "Generate my interview session →",
                type="primary",
                use_container_width=True,
            )

    if submitted:
        if not company_name.strip():
            st.error("Please enter the target company.")
        elif not job_description.strip():
            st.error("Please provide the job description.")
        elif resume_pdf is None:
            st.error("Please upload your resume PDF.")
        else:
            # A new interview invalidates results tied to the previous resume/JD.
            st.session_state.interview_result = None
            st.session_state.skill_gap_report = None
            st.session_state.skill_gap_error = None
            st.session_state.answer_feedback = {}
            st.session_state.evaluation_history = {}
            st.session_state.last_evaluated_question_index = None
            st.session_state.roadmap_completed = set()

            try:
                with st.status("Preparing your interview session...", expanded=True) as status:
                    start_time = time.perf_counter()

                    def progress_callback(message: str) -> None:
                        status.write(message)

                    interview_result = prepare_interview(
                        company_name=company_name.strip(),
                        job_description=job_description.strip(),
                        resume_pdf=resume_pdf,
                        progress_callback=progress_callback,
                    )
                    elapsed = time.perf_counter() - start_time
                    status.update(
                        label=f"Interview ready · {elapsed:.0f} seconds",
                        state="complete",
                        expanded=False,
                    )

                st.session_state.interview_result = interview_result
                if interview_result and interview_result.get("skill_gap_report"):
                    st.session_state.skill_gap_report = interview_result["skill_gap_report"]
                st.session_state.interview_id += 1
                record_interview_created(
                    company=company_name.strip(),
                    role=(interview_result.get("job_info") or {}).get("role", "")
                )
                save_session_cache(st.session_state)
                st.success("Your interview session is ready! Skill-gap analysis has also been prepared.")
                st.rerun()
            except Exception as error:
                st.error("We couldn't prepare your interview. Please review your inputs and try again.")
                with st.expander("Technical error details"):
                    st.exception(error)

    if result:
        st.divider()
        st.markdown(f"### Questions for your {result.get('company_name', '')} interview")
        questions = result.get("questions", [])
        technical_count = sum(q.get("type", "").lower() == "technical" for q in questions)
        behavioral_count = sum(q.get("type", "").lower() == "behavioral" for q in questions)
        stat_cols = st.columns(3)
        stat_cols[0].metric("Total questions", len(questions))
        stat_cols[1].metric("Technical", technical_count)
        stat_cols[2].metric("Behavioral", behavioral_count)

        st.info("Answer questions in your own words. Submit each response to receive rubric scores, supporting evidence and practical suggestions.")

        for index, question in enumerate(questions, start=1):
            question_type = str(question.get("type", "technical")).lower()
            feedback_key = f"{st.session_state.interview_id}_{index}"
            attempt_key = f"attempt_count_{st.session_state.interview_id}_{index}"
            curr_attempts = st.session_state.get(attempt_key, 0)
            saved_feedback = st.session_state.answer_feedback.get(feedback_key)

            question_title = f"Question {index:02d} · {question_type.title()}"
            if saved_feedback:
                question_title += f" · {saved_feedback.get('score', 0)}/10"
            if curr_attempts > 0:
                question_title += f" (Attempt #{curr_attempts})"

            with st.expander(question_title, expanded=(index == 1 or st.session_state.last_evaluated_question_index == index)):
                st.markdown(f"#### {question.get('question', 'Question text unavailable')}")
                st.caption("Why this question is relevant")
                st.write(question.get("reason", "Personalized for this role."))

                if curr_attempts > 0:
                    st.caption(f"🔄 Practice attempts for this question: **{curr_attempts}**")

                answer_key = f"candidate_answer_{st.session_state.interview_id}_{index}"

                with st.form(key=f"answer_form_{st.session_state.interview_id}_{index}"):
                    candidate_answer = st.text_area(
                        "Your answer",
                        key=answer_key,
                        height=160,
                        placeholder="Type your answer here. Provide structured technical explanations and real-world examples (use the STAR method for behavioral questions).",
                    )
                    evaluate_clicked = st.form_submit_button(
                        "Evaluate my answer",
                        type="primary",
                        use_container_width=True,
                    )

                if evaluate_clicked:
                    if not candidate_answer or not candidate_answer.strip():
                        st.warning("Write your answer before requesting an evaluation.")
                    elif question_type not in {"technical", "behavioral"}:
                        st.error(f"Unsupported question type: {question_type}.")
                    else:
                        job_context = json.dumps(
                            {
                                "company_name": result.get("company_name", ""),
                                "job_info": result.get("job_info", {}),
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                        try:
                            with st.spinner("Evaluating your answer against the scoring rubric..."):
                                feedback = evaluate_answer(
                                    question=question.get("question", ""),
                                    answer=candidate_answer.strip(),
                                    job_context=job_context,
                                    question_type=question_type,
                                )
                            st.session_state.answer_feedback[feedback_key] = feedback
                            st.session_state.evaluation_history[feedback_key] = {
                                "question": question.get("question", ""),
                                "question_type": question_type,
                                "score": feedback.get("score", 0),
                                "breakdown": feedback.get("breakdown", {}),
                            }
                            st.session_state.last_evaluated_question_index = index
                            st.session_state[attempt_key] = curr_attempts + 1

                            # Track attempt history for candidate review
                            attempts_hist = st.session_state.setdefault("all_attempts_history", {})
                            q_attempts = attempts_hist.setdefault(feedback_key, [])
                            q_attempts.append({
                                "attempt": curr_attempts + 1,
                                "answer": candidate_answer.strip(),
                                "score": feedback.get("score", 0),
                                "time": time.strftime("%H:%M"),
                            })

                            # Record input to user account profile
                            record_user_answer_input(
                                question=question.get("question", ""),
                                score=feedback.get("score", 7),
                                company=result.get("company_name", ""),
                            )

                            save_session_cache(st.session_state)
                            st.success(f"Your answer has been evaluated (Attempt #{curr_attempts + 1}).")
                        except Exception as error:
                            st.error("We couldn't evaluate this answer. No score was assigned.")
                            st.caption(f"Technical detail: {type(error).__name__}: {error}")

                saved_feedback = st.session_state.answer_feedback.get(feedback_key)
                if saved_feedback is not None:
                    st.divider()
                    render_answer_feedback(saved_feedback)

                    # View past attempts if candidate answered multiple times
                    past_attempts = st.session_state.get("all_attempts_history", {}).get(feedback_key, [])
                    if len(past_attempts) > 1:
                        with st.expander(f"📜 View past attempts ({len(past_attempts)} total)"):
                            for p_att in past_attempts[:-1]:
                                st.markdown(f"**Attempt #{p_att['attempt']}** · Score: `{p_att['score']}/10` · *{p_att.get('time', '')}*")
                                st.caption(p_att["answer"][:300] + ("..." if len(p_att["answer"]) > 300 else ""))
                                st.divider()

                    if st.button("🧠 Practise adaptive follow-up for this question →", key=f"quick_followup_{index}"):
                        st.session_state["_selected_followup_question_idx"] = index
                        navigate_to("Adaptive Follow-ups")

        skill_report = st.session_state.skill_gap_report or result.get("skill_gap_report")
        if skill_report:
            with st.expander("📊 Resume–JD Skill Alignment & Evidence (Analyzed in Session)", expanded=False):
                render_skill_gap_report(skill_report)
        with st.expander("🌐 Company research", expanded=False):
            st.markdown(result.get("company_research", "No company research was returned."))
        with st.expander("📋 Extracted job information", expanded=False):
            st.json(result.get("job_info", {}))
        with st.expander("📄 Resume processing summary", expanded=False):
            st.success("Resume text extracted successfully.")
            st.write("Extracted characters:", len(result.get("resume_text", "")))
    else:
        st.info("No interview session yet. Complete the form above to generate your personalized questions.")


# ============================================================
# 7. ROUTING FALLBACK
# ============================================================

elif selected_page == "Skill Gap Analysis":
    navigate_to("Interview Practice")
    st.rerun()


# ============================================================
# 8. PAGE: PERFORMANCE ANALYTICS
# ============================================================

elif selected_page == "Performance Analytics":
    render_page_header(
        "03 / MEASURE YOUR PROGRESS",
        "Performance Analytics",
        "Review scores and rubric-level feedback from the answers you have submitted in this interview session.",
    )

    active_account = get_active_account()
    acc_stats = active_account.get("stats", {})

    with st.container(border=True):
        p_col1, p_col2, p_col3, p_col4 = st.columns([1.5, 1, 1, 1])
        with p_col1:
            st.markdown(f"### 👤 {active_account.get('name', 'Candidate')}")
            st.caption(f"Profile: **{active_account.get('target_role', 'Software Engineer')}**")
        with p_col2:
            render_stat("TOTAL INPUTS", acc_stats.get("total_inputs", 0))
        with p_col3:
            render_stat("TOTAL INTERVIEWS", acc_stats.get("total_interviews", 0))
        with p_col4:
            render_stat("LIFETIME AVG", f"{acc_stats.get('average_score', 0.0)}/10" if acc_stats.get("scores_history") else "—")

    rep_btn_col1, rep_btn_col2 = st.columns([2.5, 1.5])
    with rep_btn_col2:
        if st.button("📄 Generate & Export PDF Report →", key="perf_export_report_btn", use_container_width=True):
            navigate_to("Interview Report")

    evaluations = get_current_evaluations()
    if not evaluations:
        st.info("No evaluated answers yet. Complete an answer evaluation in Interview Practice to populate this dashboard.")
        if st.button("Practise an interview question →", type="primary"):
            navigate_to("Interview Practice")
    else:
        score_values = [float(item.get("score", 0)) for item in evaluations]
        average_score = sum(score_values) / len(score_values)
        highest_score = max(score_values)
        lowest_score = min(score_values)

        metric_cols = st.columns(4)
        metric_cols[0].metric("Answers evaluated", len(evaluations))
        metric_cols[1].metric("Average score", f"{average_score:.1f}/10")
        metric_cols[2].metric("Highest score", f"{highest_score:.1f}/10")
        metric_cols[3].metric("Lowest score", f"{lowest_score:.1f}/10")

        st.markdown("### Answer score trend")
        st.bar_chart({"Score out of 10": score_values}, y_label="Score", x_label="Evaluated answers")

        st.markdown("### Performance by rubric criterion")
        criterion_totals = defaultdict(float)
        criterion_maximums = defaultdict(float)
        for item in evaluations:
            for criterion, detail in item.get("breakdown", {}).items():
                criterion_totals[criterion] += float(detail.get("score", 0))
                criterion_maximums[criterion] += float(detail.get("maximum", 0))

        criterion_percentages = {
            criterion.replace("_", " ").title(): round(
                100 * criterion_totals[criterion] / criterion_maximums[criterion], 1
            )
            for criterion in criterion_totals
            if criterion_maximums[criterion]
        }
        if criterion_percentages:
            criterion_chart_data = {
                "Criterion": list(criterion_percentages.keys()),
                "Score (%)": list(criterion_percentages.values()),
            }
            st.bar_chart(
                criterion_chart_data,
                x="Criterion",
                y="Score (%)",
                y_label="Percentage of available marks",
            )

        st.markdown("### Evaluated answers")
        for index, item in enumerate(evaluations, start=1):
            with st.expander(f"Answer {index} · {item.get('question_type', 'Interview').title()} · {item.get('score', 0)}/10"):
                st.write(item.get("question", "Question unavailable"))
                st.progress(min(max(float(item.get("score", 0)) / 10, 0.0), 1.0))

    recent_activity = active_account.get("recent_activity", [])
    if recent_activity:
        st.markdown("### 📜 Candidate activity history")
        with st.expander(f"View activity history for {active_account.get('name', 'Candidate')} ({len(recent_activity)} events)", expanded=False):
            for act in recent_activity[:20]:
                atype = act.get("type", act.get("action", "Activity")).replace("_", " ").title()
                atime = act.get("timestamp", "")[:16].replace("T", " ")
                detail_str = ""
                if "company" in act:
                    detail_str += f"Company: **{act['company']}** "
                if "role" in act and act["role"]:
                    detail_str += f"· Role: *{act['role']}* "
                if "question" in act:
                    detail_str += f"· Question: *{act['question']}...* "
                if "score" in act:
                    detail_str += f"· Score: `{act['score']}/10` "
                if "challenge" in act:
                    detail_str += f"· Challenge: **{act['challenge']}** ({'Passed' if act.get('all_passed') else 'Needs Work'}) "
                if "detail" in act:
                    detail_str += f"· {act['detail']} "
                st.markdown(f"**{atype}** · `{atime}`  \n{detail_str}")
                st.divider()


# ============================================================
# 9. PAGE: LEARNING ROADMAP
# ============================================================

elif selected_page == "Learning Roadmap":
    render_page_header(
        "04 / PLAN YOUR NEXT STEPS",
        "Personalized Learning Roadmap",
        "Turn identified skill gaps and target role requirements into an actionable, phased preparation roadmap.",
    )

    result = st.session_state.interview_result
    report = st.session_state.skill_gap_report or (result.get("skill_gap_report") if result else None)

    if not report and not result:
        st.info("No interview session found yet. Generate an interview session first to unlock your personalized learning roadmap.")
        if st.button("🎯 Build interview session →", type="primary"):
            navigate_to("Interview Practice")
    elif not report and result:
        st.info("Preparing skill alignment data for your learning roadmap...")
        try:
            with st.spinner("Analyzing skill match from your active session..."):
                report = analyze_candidate_skill_gap(
                    resume_text=result.get("resume_text", ""),
                    job_info=result.get("job_info", {}),
                )
                st.session_state.skill_gap_report = report
                st.rerun()
        except Exception as err:
            st.error(f"Could not prepare skill gap data: {err}")
    else:
        company = (result.get("company_name") if result else "") or "Target Company"
        job_info = (result.get("job_info") if result else {}) or {}

        # Top controls bar: timeline & refresh
        ctrl_cols = st.columns([1.2, 1.2, 1.6])
        with ctrl_cols[0]:
            timeline_str = st.selectbox(
                "Preparation Timeline",
                ["2 Weeks (Sprint)", "4 Weeks (Standard)", "8 Weeks (Deep Dive)"],
                index=1,
                key="roadmap_timeline_select",
            )
            timeline_weeks = 2 if "2" in timeline_str else (8 if "8" in timeline_str else 4)

        with ctrl_cols[1]:
            generation_mode = st.selectbox(
                "Generation Engine",
                ["AI-Synthesized (Ollama Qwen)", "Fast Structured Fallback"],
                index=0,
                key="roadmap_gen_mode",
            )
            use_llm = "AI" in generation_mode

        with ctrl_cols[2]:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            regen_clicked = st.button("⚡ Generate / Refresh Roadmap", type="primary", use_container_width=True)

        # Generate roadmap if not cached or requested
        current_roadmap = st.session_state.get("learning_roadmap")
        cached_timeline = st.session_state.get("_roadmap_cached_timeline")

        if regen_clicked or not current_roadmap or cached_timeline != timeline_weeks:
            with st.spinner("Synthesizing your personalized learning roadmap with milestones and project ideas..."):
                current_roadmap = generate_candidate_roadmap(
                    skill_gap_report=report,
                    job_info=job_info,
                    company_name=company,
                    timeline_weeks=timeline_weeks,
                    use_llm=use_llm,
                )
                st.session_state["learning_roadmap"] = current_roadmap
                st.session_state["_roadmap_cached_timeline"] = timeline_weeks
                record_roadmap_generated(company=company)
                save_session_cache(st.session_state)

        # Summary and Stats Banner
        phases = current_roadmap.get("phases", [])
        all_milestones = [m for p in phases for m in p.get("milestones", [])]
        total_milestones = len(all_milestones)
        completed_count = len([m for m in all_milestones if m.get("id") in st.session_state.roadmap_completed])
        progress_val = (completed_count / total_milestones) if total_milestones > 0 else 0.0

        with st.container(border=True):
            banner_col1, banner_col2, banner_col3, banner_col4 = st.columns([1.5, 1, 1, 1])
            with banner_col1:
                st.markdown(f"### 🎯 {current_roadmap.get('target_role', 'Target Role')}")
                st.caption(f"Target Company: **{current_roadmap.get('company_name', company)}**")
            with banner_col2:
                render_stat("PREP TIMELINE", f"{timeline_weeks} Weeks")
            with banner_col3:
                render_stat("SKILL READINESS", f"{current_roadmap.get('readiness_score', 0)}%")
            with banner_col4:
                render_stat("PROGRESS", f"{completed_count}/{total_milestones} Done")

            st.write(current_roadmap.get("summary", ""))
            st.progress(progress_val)
            if completed_count == total_milestones and total_milestones > 0:
                st.balloons()
                st.success("🎉 Outstanding! You have completed all milestones in your learning roadmap.")

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Phased Milestones Display
        st.markdown("### 📅 Phased preparation milestones")
        phase_tabs = st.tabs([p.get("title", f"Phase {idx+1}") for idx, p in enumerate(phases)])

        for p_idx, phase in enumerate(phases):
            with phase_tabs[p_idx]:
                st.markdown(f"**Goal:** *{phase.get('goal', '')}*")
                milestones = phase.get("milestones", [])
                if not milestones:
                    st.info("No milestones in this phase.")
                for m in milestones:
                    m_id = m.get("id", f"m_{p_idx}")
                    is_done = m_id in st.session_state.roadmap_completed
                    priority = m.get("priority", "High")
                    badge_color = "#e53e3e" if priority == "Critical" else ("#dd6b20" if priority == "High" else "#3182ce")

                    with st.container(border=True):
                        c_box, c_badge = st.columns([4, 1])
                        with c_box:
                            checked = st.checkbox(
                                f"**{m.get('skill', 'Skill')}** · {m.get('task', '')}",
                                value=is_done,
                                key=f"cb_{st.session_state.interview_id}_{m_id}",
                            )
                            if checked != is_done:
                                if checked:
                                    st.session_state.roadmap_completed.add(m_id)
                                else:
                                    st.session_state.roadmap_completed.discard(m_id)
                                save_session_cache(st.session_state)
                                st.rerun()
                        with c_badge:
                            st.markdown(
                                f"<span style='background-color:{badge_color}22; color:{badge_color}; padding:3px 8px; border-radius:12px; font-weight:600; font-size:12px; float:right;'>{priority} Priority</span>",
                                unsafe_allow_html=True,
                            )

                        st.markdown(f"**Action Plan:** {m.get('action_item', '')}")

                        proj = m.get("project_or_exercise")
                        if proj:
                            st.markdown(f"🛠️ **Portfolio Project / Exercise:** {proj}")

                        res = m.get("resource")
                        if isinstance(res, dict) and res.get("url"):
                            st.markdown(f"📖 **Curated Resource:** [{res.get('title', 'Learning Resource')}]({res.get('url')})")

                        chk = m.get("interview_check")
                        if chk:
                            with st.expander(f"🎯 Interview Verification Question for {m.get('skill')}"):
                                st.write(chk)
                                st.caption("💡 Test your ability to answer this in an interview before checking off this milestone.")

        # Company Culture Spotlight
        comp_prep = current_roadmap.get("company_prep", {})
        if comp_prep:
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"### 🏢 {comp_prep.get('company', company)} Interview Spotlight")
                st.write(comp_prep.get("key_focus", ""))
                st.info(f"💡 **Coach Advice:** {comp_prep.get('advice', '')}")

        # Quick Tips & Download
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        col_tips, col_dl = st.columns([2, 1])
        with col_tips:
            st.markdown("### 💡 High-yield interview tips")
            for tip in current_roadmap.get("quick_tips", []):
                st.markdown(f"- {tip}")
        with col_dl:
            st.markdown("### 📥 Save your plan")
            st.caption("Export your personalized roadmap as a markdown guide.")
            md_content = roadmap_to_markdown(current_roadmap)
            st.download_button(
                "Download Roadmap (.md)",
                data=md_content,
                file_name=f"prepsense_roadmap_{company.lower().replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ============================================================
# 10. PAGE: ADAPTIVE FOLLOW-UPS
# ============================================================

elif selected_page == "Adaptive Follow-ups":
    render_page_header(
        "05 / GO ONE LEVEL DEEPER",
        "Adaptive Follow-up Questions",
        "An interviewer responds directly to what you said—probing technical trade-offs, edge cases, and architectural choices.",
    )

    result = st.session_state.interview_result
    if not result:
        st.info("Generate an interview session first to practice adaptive follow-ups against your questions.")
        if st.button("Go to interview practice →", type="primary"):
            navigate_to("Interview Practice")
    else:
        questions = result.get("questions", [])
        if not questions:
            st.info("No questions in this interview session yet.")
        else:
            labels = [f"Q{index + 1}: {item.get('question', '')[:95]}" for index, item in enumerate(questions)]
            default_q_idx = st.session_state.get("_selected_followup_question_idx", 0)
            if default_q_idx >= len(labels):
                default_q_idx = 0

            selected_index = st.selectbox(
                "Choose an interview question to build on",
                range(len(labels)),
                index=default_q_idx,
                format_func=lambda value: labels[value],
            )
            selected_question = questions[selected_index]
            q_text = selected_question.get("question", "")
            q_type = selected_question.get("type", "technical")
            i_id = st.session_state.get("interview_id", 0)
            followup_state_key = f"followup_{i_id}_{selected_index}"

            st.markdown("#### Original interview question")
            st.info(f"**[{q_type.upper()}]** {q_text}")

            # Check if answer was previously drafted or evaluated in Interview Practice
            practice_answer_key = f"candidate_answer_{i_id}_{selected_index}"
            prefill_answer = st.session_state.get(practice_answer_key, "")

            answer_text = st.text_area(
                "Your original answer (review or refine before probing)",
                value=prefill_answer,
                placeholder="Paste or write your answer here so the interviewer can evaluate your claims...",
                height=130,
                key=f"adaptive_followup_answer_input_{selected_index}",
            )

            col_gen, col_clear = st.columns([2, 1])
            with col_gen:
                gen_clicked = st.button("🧠 Generate targeted follow-up question", type="primary", use_container_width=True)
            with col_clear:
                if st.button("Reset follow-up", use_container_width=True):
                    st.session_state.adaptive_followups.pop(followup_state_key, None)
                    st.rerun()

            if gen_clicked:
                if not answer_text.strip():
                    st.warning("Please provide an answer first so the interviewer has context to probe.")
                else:
                    with st.spinner("Interviewer is analyzing your response and formulating a targeted follow-up..."):
                        followup_data = generate_adaptive_followup(
                            original_question=q_text,
                            candidate_answer=answer_text.strip(),
                            job_context=result.get("job_info", {}).get("job_title", ""),
                            question_type=q_type,
                            company=result.get("company_name", ""),
                        )
                        st.session_state.adaptive_followups[followup_state_key] = followup_data
                        record_adaptive_followup(
                            original_question=q_text,
                            followup_question=followup_data.get("followup_question", ""),
                        )
                        save_session_cache(st.session_state)

            current_followup = st.session_state.adaptive_followups.get(followup_state_key)
            if current_followup:
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown(f"#### 🎯 Interviewer Follow-up · *{current_followup.get('probe_focus', 'Technical Depth')}*")
                    st.markdown(f"### {current_followup.get('followup_question')}")
                    st.caption(f"**Why the interviewer asks this:** {current_followup.get('reasoning')}")

                    with st.expander("💡 Suggested response structure & key points"):
                        st.write(current_followup.get("suggested_approach", ""))

                st.markdown("#### Your response to the follow-up")
                fu_ans_key = f"fu_resp_{i_id}_{selected_index}"
                fu_answer = st.text_area(
                    "Answer the follow-up question",
                    height=130,
                    placeholder="Address the specific edge case, trade-off, or failure condition probed above...",
                    key=fu_ans_key,
                )

                if st.button("Evaluate follow-up response", type="primary", key=f"btn_eval_fu_{selected_index}"):
                    if not fu_answer.strip():
                        st.warning("Please write an answer before evaluating.")
                    else:
                        with st.spinner("Evaluating your follow-up answer against the rubric..."):
                            fu_eval = evaluate_answer(
                                question=current_followup.get("followup_question", ""),
                                answer=fu_answer.strip(),
                                job_context=result.get("job_info", {}).get("job_title", ""),
                                question_type=q_type,
                            )
                            st.session_state[f"fu_eval_{i_id}_{selected_index}"] = fu_eval
                            record_user_answer_input(
                                question=current_followup.get("followup_question", "")[:80],
                                score=fu_eval.get("score", 7),
                                company=result.get("company_name", ""),
                            )
                            save_session_cache(st.session_state)

                saved_fu_eval = st.session_state.get(f"fu_eval_{i_id}_{selected_index}")
                if saved_fu_eval:
                    st.divider()
                    render_answer_feedback(saved_fu_eval)


# ============================================================
# 11. PAGE: CODING INTERVIEW
# ============================================================

elif selected_page == "Coding Interview":
    render_page_header(
        "06 / PRACTISE YOUR PROBLEM SOLVING",
        "Coding Interview Workspace",
        "Solve algorithmic coding challenges with real in-browser test case execution and Senior Staff AI code reviews.",
    )

    challenge_keys = list(CODING_CHALLENGES.keys())
    challenge_titles = [CODING_CHALLENGES[k]["title"] for k in challenge_keys]

    code_left, code_right = st.columns([1, 1.35], gap="large")

    with code_left:
        st.markdown("### Challenge setup")
        selected_title_idx = st.selectbox(
            "Select coding challenge",
            range(len(challenge_titles)),
            format_func=lambda idx: challenge_titles[idx],
        )
        selected_cid = challenge_keys[selected_title_idx]
        challenge_meta = CODING_CHALLENGES[selected_cid]

        diff = challenge_meta["difficulty"]
        diff_color = "#2e7d32" if diff == "Easy" else ("#ed6c02" if diff == "Medium" else "#d32f2f")
        st.markdown(
            f"<span style='background:{diff_color}22; color:{diff_color}; padding:3px 10px; border-radius:12px; font-weight:600; font-size:12px;'>"
            f"{diff.upper()}</span> · **{challenge_meta['category']}**",
            unsafe_allow_html=True,
        )

        st.markdown("### Problem statement")
        st.write(challenge_meta["description"])

        st.markdown("### Examples")
        for ex in challenge_meta["examples"]:
            st.code(f"Input: {ex['input']}\nOutput: {ex['output']}")

    with code_right:
        st.markdown("### Solution workspace (Python 3)")
        saved_code = st.session_state.coding_sessions.get(selected_cid, challenge_meta["starter_code"])
        user_code = st.text_area(
            "Code editor",
            value=saved_code,
            height=320,
            key=f"editor_{selected_cid}",
        )
        st.session_state.coding_sessions[selected_cid] = user_code

        btn_col1, btn_col2, btn_col3 = st.columns([1.2, 1.5, 1])
        with btn_col1:
            run_clicked = st.button("▶ Run test cases", use_container_width=True)
        with btn_col2:
            submit_clicked = st.button("🚀 Submit & Review", type="primary", use_container_width=True)
        with btn_col3:
            if st.button("Reset code", use_container_width=True):
                st.session_state.coding_sessions[selected_cid] = challenge_meta["starter_code"]
                st.session_state.coding_test_results.pop(selected_cid, None)
                st.session_state.coding_reviews.pop(selected_cid, None)
                st.rerun()

        # Handle Execution
        if run_clicked or submit_clicked:
            with st.spinner("Executing solution against test cases..."):
                exec_result = run_coding_test_cases(user_code, selected_cid)
                st.session_state.coding_test_results[selected_cid] = exec_result

            if submit_clicked:
                with st.spinner("Generating Senior Staff code review (complexity, edge cases, clean code)..."):
                    review_result = review_code_solution(user_code, selected_cid, exec_result)
                    st.session_state.coding_reviews[selected_cid] = review_result
                    record_coding_challenge_completed(
                        challenge_title=challenge_meta["title"],
                        all_passed=exec_result.get("all_passed", False),
                        quality_score=review_result.get("quality_score", 7),
                    )
                    save_session_cache(st.session_state)

        # Display Test Execution Results
        test_res = st.session_state.coding_test_results.get(selected_cid)
        if test_res:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if test_res.get("error"):
                st.error(test_res["error"])
            else:
                passed_cnt = test_res.get("passed_count", 0)
                tot_cnt = test_res.get("total_count", 0)
                if test_res.get("all_passed"):
                    st.success(f"🎉 **Accepted!** Passed all {tot_cnt}/{tot_cnt} test cases.")
                else:
                    st.warning(f"⚠️ **Partially passing:** {passed_cnt}/{tot_cnt} test cases passed.")

                with st.expander("🔍 Inspect individual test case runs", expanded=not test_res.get("all_passed")):
                    for tc in test_res.get("results", []):
                        status_badge = "✅ PASS" if tc["passed"] else "❌ FAIL"
                        st.markdown(
                            f"**Test Case #{tc['test_case']}** · {status_badge} · *Runtime: {tc['runtime_ms']}ms*"
                        )
                        st.caption(f"Input: `{tc['input']}` | Expected: `{tc['expected']}` | Output: `{tc['got']}`")
                        if tc.get("error"):
                            st.caption(f"Error: `{tc['error']}`")
                        st.divider()

        # Display AI Code Review
        review_data = st.session_state.coding_reviews.get(selected_cid)
        if review_data:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                r_col1, r_col2, r_col3 = st.columns(3)
                with r_col1:
                    render_stat("TIME COMPLEXITY", review_data.get("time_complexity", "O(N)"))
                with r_col2:
                    render_stat("SPACE COMPLEXITY", review_data.get("space_complexity", "O(1)"))
                with r_col3:
                    render_stat("CODE QUALITY", f"{review_data.get('quality_score', 8)}/10")

                st.markdown(f"**Verdict:** {review_data.get('overall_verdict', '')}")

                s_col, i_col = st.columns(2)
                with s_col:
                    st.markdown("##### ✅ Strengths")
                    for s in review_data.get("strengths", []):
                        st.markdown(f"- {s}")
                with i_col:
                    st.markdown("##### 💡 Suggestions")
                    for imp in review_data.get("improvements", []):
                        st.markdown(f"- {imp}")


# ============================================================
# 12. PAGE: INTERVIEW REPORT
# ============================================================

elif selected_page == "Interview Report":
    render_page_header(
        "07 / CANDIDATE DOSSIER",
        "Candidate Interview Report",
        "Generate and export a comprehensive, print-ready dossier covering interview scores, skill alignment, rubric breakdowns, and learning roadmap.",
    )

    account = get_active_account()
    result = st.session_state.interview_result
    skill_gap_report = st.session_state.skill_gap_report or (result.get("skill_gap_report") if result else None)
    evaluation_history = st.session_state.get("evaluation_history", {})
    answer_feedback = st.session_state.get("answer_feedback", {})
    roadmap = st.session_state.get("learning_roadmap")

    report_html = build_report_html(
        account=account,
        result=result,
        skill_gap_report=skill_gap_report,
        evaluation_history=evaluation_history,
        answer_feedback=answer_feedback,
        roadmap=roadmap,
    )
    report_filename = build_report_filename(account=account, result=result)

    with st.container(border=True):
        st.markdown("### 📥 Export Candidate Report")
        st.caption("Your report is packaged as a print-optimized document. Download the file, open it in any browser, and select Print → Save as PDF.")

        btn_col1, btn_col2 = st.columns([1.5, 2])
        with btn_col1:
            st.download_button(
                label="📄 Download Report (HTML / Print to PDF)",
                data=report_html,
                file_name=report_filename,
                mime="text/html",
                type="primary",
                use_container_width=True,
            )
        with btn_col2:
            st.info("💡 **How to Save as PDF:** Open the downloaded HTML file in your web browser, press `Ctrl + P` (or `Cmd + P` on Mac), select **'Save as PDF'**, and click Save.")

    st.markdown("### 👁️ Live Dossier Preview")
    import streamlit.components.v1 as components
    components.html(report_html, height=750, scrolling=True)


# ============================================================
# 13. GLOBAL FOOTER
# ============================================================

render_footer()
