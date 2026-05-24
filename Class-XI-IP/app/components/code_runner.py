"""
Sandboxed Python code runner for IP Learn.
Executes student code in a subprocess with a timeout.
"""
import subprocess
import sys
import tempfile
import os
from dataclasses import dataclass, field


@dataclass
class RunResult:
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    exit_code: int = 0

    @property
    def success(self) -> bool:
        return not self.timed_out and self.exit_code == 0


def run_code(code: str, timeout: int = 10, stdin_values: list | None = None) -> RunResult:
    """
    Write code to a temp file, execute it with the current Python interpreter,
    capture stdout/stderr, and clean up. Returns a RunResult.

    stdin_values: if provided, input() calls are served from this list in order.
    """
    tmp_path = None
    try:
        # Build the mock preamble if stdin values are provided
        if stdin_values:
            escaped = repr(stdin_values)
            mock_preamble = (
                "import builtins as _iplearn_bl\n"
                f"_iplearn_inputs = iter({escaped})\n"
                "def _iplearn_input(prompt=''):\n"
                "    val = next(_iplearn_inputs, '')\n"
                "    print(prompt, end='', flush=True)\n"
                "    print(val)\n"
                "    return val\n"
                "_iplearn_bl.input = _iplearn_input\n\n"
            )
        else:
            mock_preamble = ""

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(mock_preamble + code)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return RunResult(
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResult(stdout="", stderr="", timed_out=True, exit_code=-1)
    except Exception as exc:
        return RunResult(stdout="", stderr=str(exc), timed_out=False, exit_code=-1)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
