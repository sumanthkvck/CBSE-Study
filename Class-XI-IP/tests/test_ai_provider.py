"""Tests for AI provider — must work in offline mode."""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.provider import ask, OFFLINE_MSG, has_any_key, active_provider


def test_offline_mode_returns_friendly_message(monkeypatch):
    """With no API keys, ask() returns OFFLINE_MSG, not an exception."""
    monkeypatch.delenv("GEMINI_API_KEY",    raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY",    raising=False)
    result = ask("test prompt")
    assert result == OFFLINE_MSG


def test_offline_has_any_key_false(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY",    raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY",    raising=False)
    assert has_any_key() is False


def test_offline_active_provider(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY",    raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY",    raising=False)
    assert active_provider() == "offline"
