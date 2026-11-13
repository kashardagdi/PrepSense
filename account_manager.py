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
        local_path.touch(exist_ok=True)
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
            "average_score": 0.0,
            "scores_history": [],
        },
        "recent_activity": [],
    }


def load_accounts_db() -> Dict[str, Any]:
    """Load the full accounts database from storage."""
    file_path = _get_accounts_file()
    if not file_path.exists():
        default_db = {
            "active_user_id": DEFAULT_USER_ID,
            "accounts": {DEFAULT_USER_ID: _create_default_profile(DEFAULT_USER_ID, "Candidate")},
        }
        save_accounts_db(default_db)
        return default_db

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "accounts" not in data:
            default_db = {
                "active_user_id": DEFAULT_USER_ID,
                "accounts": {DEFAULT_USER_ID: _create_default_profile(DEFAULT_USER_ID, "Candidate")},
            }
            save_accounts_db(default_db)
            return default_db
        return data
    except Exception as err:
        print(f"[AccountManager] Failed to load accounts DB: {err}")
        return {
            "active_user_id": DEFAULT_USER_ID,
            "accounts": {DEFAULT_USER_ID: _create_default_profile(DEFAULT_USER_ID, "Candidate")},
        }


def save_accounts_db(data: Dict[str, Any]) -> bool:
    """Persist the accounts database to storage."""
    file_path = _get_accounts_file()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as err:
        print(f"[AccountManager] Failed to save accounts DB: {err}")
        return False


def get_active_account() -> Dict[str, Any]:
    """Retrieve the currently active user account."""
    db = load_accounts_db()
    active_id = db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.get("accounts", {})
    if active_id not in accounts:
        accounts[active_id] = _create_default_profile(active_id, "Candidate")
        save_accounts_db(db)
    return accounts[active_id]


def switch_or_create_account(
    username: str,
    name: Optional[str] = None,
    target_role: Optional[str] = None
) -> Dict[str, Any]:
    """Switch to an existing account by username or create a new one."""
    user_id = username.strip().casefold().replace(" ", "_")
    if not user_id:
        user_id = DEFAULT_USER_ID

    db = load_accounts_db()
    accounts = db.setdefault("accounts", {})

    if user_id in accounts:
        account = accounts[user_id]
        if name and name.strip():
            account["name"] = name.strip()
        if target_role and target_role.strip():
            account["target_role"] = target_role.strip()
    else:
        display_name = name.strip() if name and name.strip() else username.strip().title()
        account = _create_default_profile(user_id, display_name)
        if target_role and target_role.strip():
            account["target_role"] = target_role.strip()
        accounts[user_id] = account

    db["active_user_id"] = user_id
    save_accounts_db(db)
    return account


def record_user_answer_input(
    question: str,
    score: float,
    company: str = "",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Increment total candidate answer inputs and update performance stats.
    """
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {
        "total_inputs": 0,
        "total_interviews": 0,
        "total_skill_analyses": 0,
        "total_roadmaps_created": 0,
        "average_score": 0.0,
        "scores_history": [],
    })

    stats["total_inputs"] = stats.get("total_inputs", 0) + 1
    scores = stats.setdefault("scores_history", [])
    scores.append(round(float(score), 1))
    stats["average_score"] = round(sum(scores) / len(scores), 1)

    activity = account.setdefault("recent_activity", [])
    activity.insert(0, {
        "action": "Answer Evaluated",
        "detail": f"{company + ' · ' if company else ''}{question[:60]}... → Score: {score}/10",
        "timestamp": datetime.now().strftime("%b %d, %H:%M"),
        "score": score,
    })
    # Keep last 25 activities
    account["recent_activity"] = activity[:25]

    save_accounts_db(db)
    return account


def record_interview_created(
    company: str,
    role: str = "",
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record creation of a new personalized interview session."""
    db = load_accounts_db()
    target_id = user_id or db.get("active_user_id", DEFAULT_USER_ID)
    accounts = db.setdefault("accounts", {})

    if target_id not in accounts:
        accounts[target_id] = _create_default_profile(target_id, "Candidate")

    account = accounts[target_id]
    stats = account.setdefault("stats", {})
    stats["total_interviews"] = stats.get("total_interviews", 0) + 1

    activity = account.setdefault("recent_activity", [])
    activity.insert(0, {
        "action": "Interview Created",
        "detail": f"{company}{f' ({role})' if role else ''}",
        "timestamp": datetime.now().strftime("%b %d, %H:%M"),
    })
    account["recent_activity"] = activity[:25]

    save_accounts_db(db)
    return account


def record_skill_analysis_run(
    company: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Record execution of a skill-gap analysis."""
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
        "action": "Skill Gap Analyzed",
        "detail": f"Resume compared against {company} requirements",
        "timestamp": datetime.now().strftime("%b %d, %H:%M"),
    })
    account["recent_activity"] = activity[:25]

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
