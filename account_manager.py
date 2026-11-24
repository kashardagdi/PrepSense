"""
PrepSense - User Account and Activity Tracker.

Manages user accounts, tracks practice sessions, counts candidate answer inputs,
and persists historical evaluation performance across sessions.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional


def _get_accounts_file() -> Path:
    """Get preferred writable accounts cache file path."""
    local_path = Path(__file__).parent / ".prepsense_accounts.json"
    try:
        if local_path.exists():
            with open(local_path, "a", encoding="utf-8") as f:
                pass
        else:
            with open(local_path, "w", encoding="utf-8") as f:
                pass
        return local_path
    except Exception:
        return Path(tempfile.gettempdir()) / "prepsense_accounts.json"


ACCOUNTS_FILE = _get_accounts_file()
DEFAULT_USER_ID = "default_candidate"


def _create_default_profile(user_id: str = DEFAULT_USER_ID, name: str = "Candidate") -> Dict[str, Any]:
    return {
        "id": user_id,
        "name": name,
        "target_role": "Software Development Engineer",
        "created_at": datetime.now().isoformat(),
        "stats": {
            "total_inputs": 0,
            "total_interviews": 0,
            "total_skill_analyses": 0,
            "total_roadmaps_created": 0,
            "total_followups_practiced": 0,
            "total_coding_submissions": 0,
            "total_coding_solved": 0,
            "average_score": 0.0,
            "scores_history": [],
        },
        "recent_activity": [],
    }


def load_accounts_db() -> Dict[str, Any]:
    """Load accounts database from JSON file with resilient error handling."""
    candidates = [_get_accounts_file(), Path(__file__).parent / ".prepsense_accounts.json", Path(tempfile.gettempdir()) / "prepsense_accounts.json"]
    for target_file in candidates:
        if target_file.exists():
            try:
                data = json.loads(target_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "accounts" in data and data["accounts"]:
                    if "active_user_id" not in data:
                        data["active_user_id"] = DEFAULT_USER_ID
                    return data
            except Exception:
                continue

    initial_db = {
        "active_user_id": DEFAULT_USER_ID,
        "accounts": {
            DEFAULT_USER_ID: _create_default_profile(),
        },
    }
    save_accounts_db(initial_db)
    return initial_db


def save_accounts_db(db: Dict[str, Any]) -> None:
    """Save accounts database safely with multi-path resilience."""
    target_file = _get_accounts_file()
    payload = json.dumps(db, indent=2, ensure_ascii=False)
    saved = False
    try:
        target_file.write_text(payload, encoding="utf-8")
        saved = True
    except Exception as e:
        print(f"[AccountManager] Primary persist failed: {e}. Trying temp fallback.")

    # Always ensure temp backup stays in sync
    try:
        fallback = Path(tempfile.gettempdir()) / "prepsense_accounts.json"
        if fallback != target_file:
            fallback.write_text(payload, encoding="utf-8")
    except Exception:
        pass


def get_all_accounts() -> Dict[str, Dict[str, Any]]:
    """Return all stored candidate accounts."""
    db = load_accounts_db()
    return db.get("accounts", {})


def get_active_account() -> Dict[str, Any]:
    """Return the currently selected user profile."""
    db = load_accounts_db()
    active_id = db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})
    if active_id not in accounts:
        accounts[active_id] = _create_default_profile(active_id, "Candidate")
        save_accounts_db(db)
    return accounts[active_id]


def update_account_profile(
    user_id: str,
    name: str = "",
    target_role: str = "",
) -> Dict[str, Any]:
    """Update profile metadata (name, target role) without switching accounts."""
    clean_id = user_id.strip().lower().replace(" ", "_") or DEFAULT_USER_ID
    db = load_accounts_db()
    accounts = db.setdefault("accounts", {})
    if clean_id in accounts:
        if name.strip():
            accounts[clean_id]["name"] = name.strip()
        if target_role.strip():
            accounts[clean_id]["target_role"] = target_role.strip()
        save_accounts_db(db)
        return accounts[clean_id]
    return get_active_account()


def switch_or_create_account(
    user_id: str,
    name: str = "",
    target_role: str = "",
) -> Dict[str, Any]:
    """Switch active profile or create a new candidate account."""
    clean_id = user_id.strip().lower().replace(" ", "_") or DEFAULT_USER_ID
    db = load_accounts_db()
    accounts = db.setdefault("accounts", {})

    if clean_id not in accounts:
        accounts[clean_id] = _create_default_profile(
            user_id=clean_id,
            name=name.strip() or clean_id.capitalize(),
        )
        if target_role.strip():
            accounts[clean_id]["target_role"] = target_role.strip()
    else:
        if name.strip():
            accounts[clean_id]["name"] = name.strip()
        if target_role.strip():
            accounts[clean_id]["target_role"] = target_role.strip()

    db["active_user_id"] = clean_id
    save_accounts_db(db)
    return accounts[clean_id]


def record_user_answer_input(
    question: str,
    score: float,
    company: str = "",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record an answer evaluation submission and update candidate statistics."""
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {})

    # Increment inputs counter
    stats["total_inputs"] = stats.get("total_inputs", 0) + 1

    # Record score history and recalculate lifetime average
    scores = stats.setdefault("scores_history", [])
    scores.append(round(float(score), 1))
    stats["average_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0

    # Add to recent activity log
    activity = account.setdefault("recent_activity", [])
    activity.insert(0, {
        "type": "answer_evaluated",
        "question": question[:80],
        "score": score,
        "company": company,
        "timestamp": datetime.now().isoformat(),
    })
    account["recent_activity"] = activity[:20]

    save_accounts_db(db)
    return account


def record_interview_created(
    company: str,
    role: str = "",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record creation of a new interview session."""
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {})
    stats["total_interviews"] = stats.get("total_interviews", 0) + 1

    if role and not account.get("target_role"):
        account["target_role"] = role

    activity = account.setdefault("recent_activity", [])
    activity.insert(0, {
        "type": "interview_created",
        "company": company,
        "role": role,
        "timestamp": datetime.now().isoformat(),
    })
    account["recent_activity"] = activity[:20]

    save_accounts_db(db)
    return account


def record_skill_analysis_run(
    company: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record execution of Resume-JD skill-gap analysis."""
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {})
    stats["total_skill_analyses"] = stats.get("total_skill_analyses", 0) + 1

    activity = account.setdefault("recent_activity", [])
    activity.insert(0, {
        "type": "skill_analysis_run",
        "company": company,
        "timestamp": datetime.now().isoformat(),
    })
    account["recent_activity"] = activity[:20]

    save_accounts_db(db)
    return account


def record_roadmap_generated(
    company: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record creation/generation of a personalized learning roadmap."""
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {})
    stats["total_roadmaps_created"] = stats.get("total_roadmaps_created", 0) + 1

    save_accounts_db(db)
    return account


def record_adaptive_followup(
    original_question: str,
    followup_question: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record an adaptive follow-up generation."""
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {})
    stats["total_followups_practiced"] = stats.get("total_followups_practiced", 0) + 1

    activity = account.setdefault("recent_activity", [])
    activity.insert(0, {
        "type": "adaptive_followup",
        "question": original_question[:80],
        "followup": followup_question[:80],
        "timestamp": datetime.now().isoformat(),
    })
    account["recent_activity"] = activity[:20]

    save_accounts_db(db)
    return account


def record_coding_challenge_completed(
    challenge_title: str,
    all_passed: bool,
    quality_score: int,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a coding challenge execution and review."""
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {})
    stats["total_coding_submissions"] = stats.get("total_coding_submissions", 0) + 1
    if all_passed:
        stats["total_coding_solved"] = stats.get("total_coding_solved", 0) + 1

    activity = account.setdefault("recent_activity", [])
    activity.insert(0, {
        "type": "coding_challenge",
        "challenge": challenge_title,
        "all_passed": all_passed,
        "quality_score": quality_score,
        "timestamp": datetime.now().isoformat(),
    })
    account["recent_activity"] = activity[:20]

    save_accounts_db(db)
    return account
