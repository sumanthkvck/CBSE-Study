"""
Progress tracking for IP Learn.
Saves XP, streak, solved problems, MCQ stats, and preferences to progress.json.
"""
import json
import os
from datetime import datetime
from pathlib import Path

SAVE_FILE = Path(__file__).parent.parent.parent / "progress.json"

DEFAULT = {
    "xp": 0,
    "streak": 0,
    "last_date": "",
    "solved_coding": [],
    "mcq_correct": 0,
    "mcq_total": 0,
    "chapters_visited": [],
    "theme": "Dark",
    "ai_provider": "gemini",
    # NEW keys for wireframe-designed pages:
    "name": "",                # student name (set during onboarding)
    "onboarded": False,        # True after onboarding flow completes
    "daily_xp_goal": 50,      # XP target per day
    "chapter_progress": {},    # {str(ch_num): pct}  0-100
    "topics_done": {},         # {str(ch_num): [topic_index, ...]}
    "daily_xp": {},            # {"YYYY-MM-DD": xp_amount}
    "badges_earned": [],       # list of badge id strings
    "code_theme": "monokai",   # code editor colour theme
}


def load() -> dict:
    if SAVE_FILE.exists():
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            # merge with defaults so new keys are always present
            merged = {**DEFAULT, **data}
            return merged
        except Exception:
            pass
    return dict(DEFAULT)


def save(data: dict):
    SAVE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_xp(data: dict, amount: int) -> dict:
    data["xp"] += amount
    today = datetime.now().strftime("%Y-%m-%d")
    if data["last_date"] != today:
        data["streak"] += 1
        data["last_date"] = today
    # Track daily XP for activity chart
    data.setdefault("daily_xp", {})
    data["daily_xp"][today] = data["daily_xp"].get(today, 0) + amount
    save(data)
    return data


def mark_solved(data: dict, challenge_id: str) -> tuple:
    """Returns (updated_data, xp_awarded)."""
    already = challenge_id in data["solved_coding"]
    if not already:
        data["solved_coding"].append(challenge_id)
    xp = 5 if already else 25
    data = add_xp(data, xp)
    return data, xp


def record_mcq(data: dict, correct: bool) -> dict:
    data["mcq_total"] += 1
    if correct:
        data["mcq_correct"] += 1
        data = add_xp(data, 10)
    save(data)
    return data


def visit_chapter(data: dict, chapter_num: int) -> dict:
    if chapter_num not in data["chapters_visited"]:
        data["chapters_visited"].append(chapter_num)
        data = add_xp(data, 5)
    save(data)
    return data


def mcq_accuracy(data: dict) -> int:
    if data["mcq_total"] == 0:
        return 0
    return int(100 * data["mcq_correct"] / data["mcq_total"])


def add_daily_xp(data: dict, amount: int) -> dict:
    """Record XP earned today for the activity chart."""
    today = datetime.now().strftime("%Y-%m-%d")
    data.setdefault("daily_xp", {})
    data["daily_xp"][today] = data["daily_xp"].get(today, 0) + amount
    save(data)
    return data


def mark_topic_done(data: dict, chapter_num: int, topic_idx: int, total_topics: int) -> dict:
    """Mark a topic done (+2 XP first time) and update chapter_progress percentage."""
    ch_key = str(chapter_num)
    done_list = list(data.setdefault("topics_done", {}).get(ch_key, []))
    if topic_idx not in done_list:
        done_list.append(topic_idx)
        data["topics_done"][ch_key] = done_list
        data = add_xp(data, 2)
    pct = int(len(done_list) / max(total_topics, 1) * 100)
    data.setdefault("chapter_progress", {})[ch_key] = pct
    save(data)
    return data
