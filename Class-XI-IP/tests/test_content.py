"""Tests for chapter content JSON files."""
import json
import pytest
from pathlib import Path

CONTENT_DIR = Path(__file__).parent.parent / "app" / "content"


def load_chapter(filename):
    return json.loads((CONTENT_DIR / filename).read_text(encoding="utf-8"))


def get_all_chapter_files():
    index = json.loads((CONTENT_DIR / "index.json").read_text(encoding="utf-8"))
    return [(ch["num"], ch["file"]) for ch in index["chapters"]]


@pytest.mark.parametrize("ch_num,filename", get_all_chapter_files())
def test_chapter_has_required_fields(ch_num, filename):
    data = load_chapter(filename)
    assert "title"        in data, f"Ch {ch_num}: missing 'title'"
    assert "topics"       in data, f"Ch {ch_num}: missing 'topics'"
    assert "summary"      in data, f"Ch {ch_num}: missing 'summary'"
    assert "mcqs"         in data, f"Ch {ch_num}: missing 'mcqs'"
    assert "key_concepts" in data, f"Ch {ch_num}: missing 'key_concepts'"


@pytest.mark.parametrize("ch_num,filename", get_all_chapter_files())
def test_chapter_has_enough_mcqs(ch_num, filename):
    data = load_chapter(filename)
    assert len(data["mcqs"]) >= 8, f"Ch {ch_num}: only {len(data['mcqs'])} MCQs (need 8+)"


@pytest.mark.parametrize("ch_num,filename", get_all_chapter_files())
def test_chapter_has_enough_concepts(ch_num, filename):
    data = load_chapter(filename)
    assert len(data["key_concepts"]) >= 6, f"Ch {ch_num}: only {len(data['key_concepts'])} concepts (need 6+)"


@pytest.mark.parametrize("ch_num,filename", get_all_chapter_files())
def test_mcq_format(ch_num, filename):
    data = load_chapter(filename)
    for q in data["mcqs"]:
        qid = q.get("id", "?")
        assert "question"      in q,   f"Ch {ch_num} MCQ {qid}: missing 'question'"
        assert "options"       in q,   f"Ch {ch_num} MCQ {qid}: missing 'options'"
        assert "correct_index" in q,   f"Ch {ch_num} MCQ {qid}: missing 'correct_index'"
        assert "explanation"   in q,   f"Ch {ch_num} MCQ {qid}: missing 'explanation'"
        assert len(q["options"]) == 4, f"Ch {ch_num} MCQ {qid}: must have exactly 4 options"
        assert q["correct_index"] in range(4), f"Ch {ch_num} MCQ {qid}: correct_index must be 0-3"


@pytest.mark.parametrize("ch_num,filename", get_all_chapter_files())
def test_no_duplicate_mcq_ids(ch_num, filename):
    data = load_chapter(filename)
    ids = [q["id"] for q in data["mcqs"] if "id" in q]
    assert len(ids) == len(set(ids)), f"Ch {ch_num}: duplicate MCQ IDs found"


@pytest.mark.parametrize("ch_num,filename", get_all_chapter_files())
def test_coding_challenge_format(ch_num, filename):
    data = load_chapter(filename)
    for c in data.get("coding_challenges", []):
        cid = c.get("id", "?")
        assert "title"           in c, f"Ch {ch_num} challenge {cid}: missing 'title'"
        assert "description"     in c, f"Ch {ch_num} challenge {cid}: missing 'description'"
        assert "starter_code"    in c, f"Ch {ch_num} challenge {cid}: missing 'starter_code'"
        assert "expected_output" in c, f"Ch {ch_num} challenge {cid}: missing 'expected_output'"
        assert "hint"            in c, f"Ch {ch_num} challenge {cid}: missing 'hint'"
