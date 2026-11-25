"""
PrepSense - Persistent Session Manager.

Saves and restores active interview sessions, skill gap reports, answer evaluations,
attempts history, candidate answer drafts, and roadmap progress to/from local storage
so users never lose their work when navigating, refreshing the browser, or switching pages.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional


def _clean_user_id(user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    clean = "".join(c for c in str(user_id).lower() if c.isalnum() or c in ("_", "-")).strip()
    return clean or None


def _get_cache_file(user_id: Optional[str] = None) -> Path:
    """Get the preferred writable cache file location, optionally per-user."""
    clean_uid = _clean_user_id(user_id)
    filename = f".session_cache_{clean_uid}.json" if clean_uid else ".session_cache.json"
    local_path = Path(__file__).parent / filename
    try:
        if local_path.exists():
            with open(local_path, "a", encoding="utf-8") as f:
                pass
        else:
            with open(local_path, "w", encoding="utf-8") as f:
                pass
        return local_path
    except Exception:
        fallback_name = f"prepsense_session_cache_{clean_uid}.json" if clean_uid else "prepsense_session_cache.json"
        return Path(tempfile.gettempdir()) / fallback_name


CACHE_FILE = _get_cache_file()


def _resolve_active_user_id(user_id: Optional[str] = None) -> Optional[str]:
    if user_id:
        return _clean_user_id(user_id)
    try:
        from account_manager import get_active_account
        active = get_active_account()
        return _clean_user_id(active.get("id"))
    except Exception:
        return None


def save_session_cache(state: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """Save active interview session data to local cache file for the active or specified user."""
    try:
        target_uid = _resolve_active_user_id(user_id)
        cache_file = _get_cache_file(target_uid)

        # Extract any candidate answer drafts from session state
        interview_id = state.get("interview_id", 0)
        candidate_answers = {}
        attempt_counts = {}
        for key, val in state.items():
            if key.startswith(f"candidate_answer_{interview_id}_") and isinstance(val, str):
                candidate_answers[key] = val
            elif key.startswith(f"attempt_count_{interview_id}_"):
                attempt_counts[key] = val

        data_to_save = {
            "user_id": target_uid,
            "interview_id": interview_id,
            "interview_result": state.get("interview_result"),
            "skill_gap_report": state.get("skill_gap_report"),
            "skill_gap_error": state.get("skill_gap_error"),
            "answer_feedback": state.get("answer_feedback", {}),
            "evaluation_history": state.get("evaluation_history", {}),
            "last_evaluated_question_index": state.get("last_evaluated_question_index"),
            "roadmap_completed": list(state.get("roadmap_completed", [])),
            "learning_roadmap": state.get("learning_roadmap"),
            "nav_history": state.get("nav_history", []),
            "adaptive_followups": state.get("adaptive_followups", {}),
            "coding_sessions": state.get("coding_sessions", {}),
            "all_attempts_history": state.get("all_attempts_history", {}),
            "candidate_answers": candidate_answers,
            "attempt_counts": attempt_counts,
        }

        # Do not save if neither result nor skill gap report exists
        if not data_to_save["interview_result"] and not data_to_save["skill_gap_report"]:
            return False

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

        # Mirror to fallback general file for legacy compatibility
        try:
            gen_file = _get_cache_file(None)
            if gen_file != cache_file:
                with open(gen_file, "w", encoding="utf-8") as gf:
                    json.dump(data_to_save, gf, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return True
    except Exception as err:
        print(f"[SessionManager] Failed to save session cache: {err}")
        return False


def load_session_cache(user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load previously saved interview session data for the active or specified user."""
    target_uid = _resolve_active_user_id(user_id)
    cache_file = _get_cache_file(target_uid)

    found_file = None
    if cache_file.exists():
        try:
            if cache_file.stat().st_size > 0:
                found_file = cache_file
        except Exception:
            pass

    if not found_file:
        fallback_temp = Path(tempfile.gettempdir()) / (f"prepsense_session_cache_{target_uid}.json" if target_uid else "prepsense_session_cache.json")
        if fallback_temp.exists():
            try:
                if fallback_temp.stat().st_size > 0:
                    found_file = fallback_temp
            except Exception:
                pass

    if not found_file:
        generic = _get_cache_file(None)
        if generic.exists() and generic != cache_file:
            try:
                if generic.stat().st_size > 0:
                    found_file = generic
            except Exception:
                pass

    if not found_file:
        return None

    try:
        with open(found_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        # If data explicitly specifies a different user, ignore it when user_id was requested
        cached_uid = data.get("user_id")
        if target_uid and cached_uid and cached_uid != target_uid:
            return None

        if "roadmap_completed" in data:
            data["roadmap_completed"] = set(data["roadmap_completed"])

        return data
    except Exception as err:
        print(f"[SessionManager] Failed to load session cache: {err}")
        return None


def clear_session_cache(user_id: Optional[str] = None) -> bool:
    """Delete the saved session cache file."""
    target_uid = _resolve_active_user_id(user_id)
    cleared = False
    for uid in (target_uid, None):
        try:
            f = _get_cache_file(uid)
            if f.exists():
                f.unlink()
                cleared = True
        except Exception:
            pass
        try:
            fb = Path(tempfile.gettempdir()) / (f"prepsense_session_cache_{uid}.json" if uid else "prepsense_session_cache.json")
            if fb.exists():
                fb.unlink()
                cleared = True
        except Exception:
            pass
    return cleared


def clear_session_state_for_switch(state: Dict[str, Any]) -> None:
    """Reset session state in memory when switching user accounts."""
    defaults = {
        "interview_result": None,
        "interview_id": 0,
        "answer_feedback": {},
        "evaluation_history": {},
        "last_evaluated_question_index": None,
        "skill_gap_report": None,
        "skill_gap_error": None,
        "roadmap_completed": set(),
        "learning_roadmap": None,
        "nav_history": ["Overview"],
        "adaptive_followups": {},
        "coding_sessions": {},
        "all_attempts_history": {},
        "coding_test_results": {},
        "coding_reviews": {},
    }
    for k, v in defaults.items():
        state[k] = v

    keys_to_delete = [
        k for k in list(state.keys())
        if k.startswith("candidate_answer_") or k.startswith("attempt_count_") or k.startswith("fu_")
    ]
    for k in keys_to_delete:
        del state[k]


def restore_session_into_state(state: Dict[str, Any], user_id: Optional[str] = None) -> bool:
    """Load cached session for a user and inject into state dict."""
    cached = load_session_cache(user_id=user_id)
    if not cached or not cached.get("interview_result"):
        return False

    for k, v in cached.items():
        if k in state and v is not None:
            state[k] = v
    for ans_k, ans_v in cached.get("candidate_answers", {}).items():
        state[ans_k] = ans_v
    for att_k, att_v in cached.get("attempt_counts", {}).items():
        state[att_k] = att_v
    return True
