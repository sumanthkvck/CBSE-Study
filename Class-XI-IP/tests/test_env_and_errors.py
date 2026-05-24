"""Tests for environment detection and error logging."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_local_by_default(monkeypatch):
    monkeypatch.delenv("STREAMLIT_SHARING_MODE", raising=False)
    monkeypatch.delenv("IS_CLOUD_DEMO",          raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT",    raising=False)
    monkeypatch.delenv("RENDER",                 raising=False)
    from app.utils.env import is_cloud, can_run_code
    assert is_cloud()        is False
    assert can_run_code()    is True

def test_cloud_detected(monkeypatch):
    monkeypatch.setenv("IS_CLOUD_DEMO", "1")
    import importlib, app.utils.env
    importlib.reload(app.utils.env)
    from app.utils.env import is_cloud, can_run_code
    assert is_cloud()     is True
    assert can_run_code() is False
    monkeypatch.delenv("IS_CLOUD_DEMO")
    importlib.reload(app.utils.env)

def test_feedback_save_and_load(tmp_path, monkeypatch):
    import app.utils.feedback as fb
    monkeypatch.setattr(fb, "FEEDBACK_FILE", tmp_path / "feedback.json")
    fb.save_feedback("mcq", "Test message", "🐛 Something broke")
    entries = fb.load_feedback()
    assert len(entries) == 1
    assert entries[0]["message"]  == "Test message"
    assert entries[0]["page"]     == "mcq"
    assert entries[0]["category"] == "🐛 Something broke"

def test_error_logging(tmp_path, monkeypatch):
    import app.utils.errors as err_utils
    monkeypatch.setattr(err_utils, "LOG_DIR",  tmp_path)
    monkeypatch.setattr(err_utils, "LOG_FILE", tmp_path / "errors.log")
    try:
        raise ValueError("test error")
    except Exception as e:
        err_utils.log_error("test context", e)
    assert (tmp_path / "errors.log").exists()
    recent = err_utils.read_recent_errors(1)
    assert len(recent) == 1
    assert "test error" in recent[0]
