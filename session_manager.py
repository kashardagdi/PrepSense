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


def _get_cache_file() -> Path:
    """Get the preferred writable cache file location."""
    local_path = Path(__file__).parent / ".session_cache.json"
    try:
        local_path.touch(exist_ok=True)
        return local_path
    except Exception:
        return Path(tempfile.gettempdir()) / "prepsense_session_cache.json"


CACHE_FILE = _get_cache_file()


def save_session_cache(state: Dict[str, Any]) -> bool:
    """Save active interview session data to local cache file."""
    try:
        cache_file = _get_cache_file()

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
            "candidate_answers": candidate_answers,
            "attempt_counts": attempt_counts,
        }

        # Do not save if neither result nor skill gap report exists
        if not data_to_save["interview_result"] and not data_to_save["skill_gap_report"]:
            return False

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        return True
    except Exception as err:
        print(f"[SessionManager] Failed to save session cache: {err}")
        return False


def load_session_cache() -> Optional[Dict[str, Any]]:
    """Load previously saved interview session data from the local cache file."""
    cache_file = _get_cache_file()
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        if "roadmap_completed" in data:
            data["roadmap_completed"] = set(data["roadmap_completed"])

        return data
    except Exception as err:
        print(f"[SessionManager] Failed to load session cache: {err}")
        return None


def clear_session_cache() -> bool:
    """Delete the saved session cache file."""
    try:
        cache_file = _get_cache_file()
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False
    except Exception as err:
        print(f"[SessionManager] Failed to clear session cache: {err}")
        return False
