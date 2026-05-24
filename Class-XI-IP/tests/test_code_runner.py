"""Tests for the sandboxed Python code runner."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.components.code_runner import run_code


def test_simple_print():
    result = run_code("print('hello')")
    assert result.stdout.strip() == "hello"
    assert result.exit_code == 0


def test_syntax_error():
    result = run_code("def foo(:")
    assert result.exit_code != 0
    assert result.stderr


def test_timeout():
    result = run_code("while True: pass", timeout=2)
    assert result.timed_out is True


def test_expected_output_match():
    code = "for i in range(1, 4):\n    print(i)"
    result = run_code(code)
    assert result.stdout.strip() == "1\n2\n3"
