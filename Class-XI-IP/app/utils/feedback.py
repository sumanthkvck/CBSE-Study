"""
Feedback capture for IP Learn.
Saves daughter's feedback to feedback.json for the developer to review.
"""
import json
from datetime import datetime
from pathlib import Path

FEEDBACK_FILE = Path(__file__).parent.parent.parent / "feedback.json"

def save_feedback(page: str, message: str, category: str = "general"):
    """Append a feedback entry."""
    entries = []
    if FEEDBACK_FILE.exists():
        try:
            entries = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            entries = []

    entries.append({
        "timestamp": datetime.now().isoformat(),
        "page":      page,
        "category":  category,
        "message":   message,
    })
    FEEDBACK_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")

def load_feedback() -> list[dict]:
    if not FEEDBACK_FILE.exists():
        return []
    try:
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
