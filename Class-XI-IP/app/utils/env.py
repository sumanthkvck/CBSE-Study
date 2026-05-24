"""
Environment detection for IP Learn.
Allows the same codebase to run locally (full features) or on
Streamlit Cloud (demo mode — no code runner, in-memory progress).
"""
import os

def is_cloud() -> bool:
    """True when running on Streamlit Cloud or any hosted environment."""
    return bool(
        os.getenv("STREAMLIT_SHARING_MODE")   # set by Streamlit Cloud
        or os.getenv("IS_CLOUD_DEMO")         # set manually for other hosts
        or os.getenv("RAILWAY_ENVIRONMENT")   # Railway.app
        or os.getenv("RENDER")                # Render.com
    )

def can_run_code() -> bool:
    """True when the Python code runner is safe to use."""
    return not is_cloud()

def progress_is_persistent() -> bool:
    """True when progress.json will survive app restarts."""
    return not is_cloud()

# Human-readable labels used in the UI
CLOUD_BANNER = (
    "**Demo mode** — You're viewing IP Learn online. "
    "MCQ practice and lessons are fully functional. "
    "To run Python code challenges and save your progress permanently, "
    "[download the app](https://github.com) and run it locally."
)
