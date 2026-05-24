"""Tests for the progress tracking utilities."""
import sys
import copy
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import app.utils.progress as prog


@pytest.fixture(autouse=True)
def no_file_write(monkeypatch):
    """Prevent all tests from writing to progress.json."""
    monkeypatch.setattr(prog, "save", lambda _: None)


def fresh() -> dict:
    """Return a deep copy of DEFAULT so tests don't share mutable state."""
    return copy.deepcopy(prog.DEFAULT)


def test_add_xp():
    data = fresh()
    data = prog.add_xp(data, 50)
    assert data["xp"] == 50


def test_record_mcq_correct():
    data = fresh()
    data = prog.record_mcq(data, correct=True)
    assert data["mcq_correct"] == 1
    assert data["mcq_total"]   == 1


def test_record_mcq_wrong():
    data = fresh()
    data = prog.record_mcq(data, correct=False)
    assert data["mcq_correct"] == 0
    assert data["mcq_total"]   == 1


def test_mcq_accuracy_zero():
    data = fresh()
    assert prog.mcq_accuracy(data) == 0


def test_mcq_accuracy():
    data = {**fresh(), "mcq_correct": 7, "mcq_total": 10}
    assert prog.mcq_accuracy(data) == 70


def test_mark_solved_first_time():
    data = fresh()
    data, xp = prog.mark_solved(data, "ch05_code_001")
    assert "ch05_code_001" in data["solved_coding"]
    assert xp == 25


def test_mark_solved_repeat():
    data = {**fresh(), "solved_coding": ["ch05_code_001"]}
    data, xp = prog.mark_solved(data, "ch05_code_001")
    assert xp == 5
