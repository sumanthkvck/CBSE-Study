"""
Error capture and logging for IP Learn.
Writes errors to logs/errors.log so the developer can review them.
Shows a friendly message to the student.
"""
import traceback
import logging
from datetime import datetime
from pathlib import Path

LOG_DIR  = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "errors.log"

def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def log_error(context: str, exc: Exception):
    """Write a full traceback to errors.log."""
    LOG_DIR.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"{datetime.now()} | {context}\n")
        f.write(traceback.format_exc())
        f.write("\n")

def read_recent_errors(n: int = 5) -> list[str]:
    """Return the last n error blocks from the log."""
    if not LOG_FILE.exists():
        return []
    text   = LOG_FILE.read_text(encoding="utf-8")
    blocks = [b.strip() for b in text.split("="*60) if b.strip()]
    return blocks[-n:]
