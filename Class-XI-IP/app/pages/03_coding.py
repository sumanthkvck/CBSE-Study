"""
Coding Challenges page — IP Learn
Two views: list (chapter-grouped) → solver (split-panel)
"""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils import progress as prog_utils
from app.utils.css import inject_theme_css
from app.components.sidebar import render_sidebar
from app.components.code_runner import run_code
from app.utils.env import can_run_code

st.set_page_config(page_title="Coding Challenges — IP Learn", page_icon="💻", layout="wide")
st.session_state["_current_page"] = "coding"

CONTENT_DIR = Path(__file__).parent.parent / "content"

CHAPTERS = [
    {"num": 1,  "title": "Introduction to Computer System", "file": "ch01_computer_system.json"},
    {"num": 2,  "title": "Programming with Python",          "file": "ch02_programming_python.json"},
    {"num": 3,  "title": "Python Basics",                    "file": "ch03_python_basics.json"},
    {"num": 4,  "title": "Data Types and Operators",         "file": "ch04_data_types_operators.json"},
    {"num": 5,  "title": "Control Flow Statements",          "file": "ch05_control_flow.json"},
    {"num": 6,  "title": "List Manipulation",                "file": "ch06_lists.json"},
    {"num": 7,  "title": "Python Dictionary",                "file": "ch07_dictionary.json"},
    {"num": 8,  "title": "Database Concepts",                "file": "ch08_database_concepts.json"},
    {"num": 9,  "title": "Structured Query Language",        "file": "ch09_sql.json"},
    {"num": 10, "title": "Emerging Trends in Technology",    "file": "ch10_emerging_trends.json"},
]

DIFF_COLOR = {"Easy": "#27ae60", "Medium": "#e67e22", "Hard": "#c0392b"}

# ── Bootstrap ──────────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = prog_utils.load()

render_sidebar(st.session_state.progress)
inject_theme_css(st.session_state.progress.get("theme", "Dark"))

# Consume pre-filter from Learn page
st.session_state.pop("coding_chapter_filter", None)

# Session state defaults
_defaults = {
    "coding_view": "list",
    "current_challenge_id": None,
    "attempt_count": 0,
    "show_hint": False,
    "show_solution": False,
    "last_result": None,
    "test_results": [],
    "solved_this_session": set(),
    "_coding_diff_filter": "All",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Extra CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Pill filter buttons */
div[data-testid="column"] .stButton > button {
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
}
/* Code textarea */
textarea {
    font-family: ui-monospace, 'Cascadia Code', 'Fira Code', monospace !important;
    font-size: 13px !important;
    line-height: 1.55 !important;
}
/* Challenge card */
.ch-card {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 6px;
    min-height: 80px;
}
/* Difficulty pill */
.diff-pill {
    display: inline-block;
    border-radius: 999px;
    padding: 1px 9px;
    font-size: 11px;
    font-weight: 700;
    margin-top: 4px;
}
/* Scribble underline */
.scribble-line {
    height: 3px;
    border-radius: 2px;
    background: var(--accent);
    margin: 4px 0 14px 0;
    width: 40px;
}
/* Output box */
.output-box {
    background: var(--code-bg);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
    font-family: ui-monospace, monospace;
    font-size: 13px;
    margin-bottom: 10px;
    white-space: pre-wrap;
    color: #ABB2BF;
}
/* Info box */
.info-box {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
/* Test case box */
.test-box {
    background: #FFF8E0;
    border: 1.5px solid #E09000;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
    color: #1a1a1a;
}
</style>
""", unsafe_allow_html=True)


# ── Data helpers ───────────────────────────────────────────────────────────────

@st.cache_data
def load_chapter_challenges(filename: str) -> list:
    path = CONTENT_DIR / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("coding_challenges", [])
    except Exception:
        return []


def all_challenges() -> list:
    """All challenges tagged with chapter info."""
    result = []
    for ch in CHAPTERS:
        for c in load_chapter_challenges(ch["file"]):
            c = dict(c)
            c["_ch_num"]   = ch["num"]
            c["_ch_title"] = ch["title"]
            result.append(c)
    return result


def find_challenge(challenge_id: str):
    for c in all_challenges():
        if c["id"] == challenge_id:
            return c
    return None


def challenge_index_in_chapter(challenge_id: str) -> int:
    """1-based position of this challenge within its chapter."""
    ch_num = None
    for c in all_challenges():
        if c["id"] == challenge_id:
            ch_num = c["_ch_num"]
            break
    if ch_num is None:
        return 1
    idx = 0
    for c in all_challenges():
        if c["_ch_num"] == ch_num:
            idx += 1
            if c["id"] == challenge_id:
                return idx
    return 1


def build_test_cases(challenge: dict) -> list:
    """Use explicit test_cases if present; fall back to expected_output."""
    if challenge.get("test_cases"):
        return list(challenge["test_cases"])
    expected = challenge.get("expected_output", "").strip()
    if expected:
        return [{"label": "Expected output", "expected_output": expected}]
    return []


def _pill_row(options, current, key_prefix) -> str:
    cols = st.columns(len(options))
    selected = current
    for i, opt in enumerate(options):
        btn_type = "primary" if str(current) == str(opt) else "secondary"
        if cols[i].button(str(opt), key=f"{key_prefix}_{opt}", type=btn_type, use_container_width=True):
            selected = opt
    return selected


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — CHALLENGES LIST
# ══════════════════════════════════════════════════════════════════════════════

def render_list():
    st.markdown("## Python challenges")
    st.markdown(
        '<p style="color:var(--subtext);margin-top:-8px;margin-bottom:18px">'
        "Solve, run, level up — all in your browser.</p>",
        unsafe_allow_html=True,
    )

    challenges  = all_challenges()
    solved_ids  = set(st.session_state.progress.get("solved_coding", []))
    total       = len(challenges)
    solved_count = sum(1 for c in challenges if c["id"] in solved_ids)

    # ── Filter + progress row ─────────────────────────────────────────────
    filter_col, prog_col = st.columns([2, 1.5])

    with filter_col:
        new_diff = _pill_row(
            ["All", "Easy", "Medium", "Hard"],
            st.session_state["_coding_diff_filter"],
            "diff_filter",
        )
        if new_diff != st.session_state["_coding_diff_filter"]:
            st.session_state["_coding_diff_filter"] = new_diff
            st.rerun()

    with prog_col:
        pct = int(solved_count / total * 100) if total else 0
        st.markdown(
            f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">'
            f'<span style="font-size:13px;font-weight:600;color:var(--subtext)">'
            f'{solved_count} / {total} solved</span>'
            f'<div style="width:180px;height:8px;background:var(--border);border-radius:999px;overflow:hidden">'
            f'<div style="width:{pct}%;height:100%;background:var(--success);border-radius:999px"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    diff_filter = st.session_state["_coding_diff_filter"]
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Chapters ──────────────────────────────────────────────────────────
    for ch in CHAPTERS:
        ch_challenges = [c for c in challenges if c["_ch_num"] == ch["num"]]
        if diff_filter != "All":
            ch_challenges = [c for c in ch_challenges if c.get("difficulty") == diff_filter]
        if not ch_challenges:
            continue

        hdr_l, hdr_r = st.columns([5, 1])
        with hdr_l:
            st.markdown(
                f'<div style="font-size:18px;font-weight:700;margin-bottom:2px">'
                f'ch.{ch["num"]:02d} · {ch["title"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="scribble-line"></div>', unsafe_allow_html=True)
        with hdr_r:
            st.markdown(
                f'<div style="text-align:right;margin-top:4px;font-size:13px;'
                f'color:var(--subtext)">'
                f'{len(ch_challenges)} challenge{"s" if len(ch_challenges) != 1 else ""}'
                f'</div>',
                unsafe_allow_html=True,
            )

        card_cols = st.columns(2)
        for i, challenge in enumerate(ch_challenges):
            col  = card_cols[i % 2]
            cid  = challenge["id"]
            is_solved = cid in solved_ids
            diff      = challenge.get("difficulty", "Easy")
            diff_color = DIFF_COLOR.get(diff, "var(--subtext)")

            status_icon = "✅" if is_solved else "○"
            bg = "#E6FFE6" if is_solved else "var(--surface)"
            brd = "#27ae60" if is_solved else "var(--border)"
            tc = "#1a1a1a" if is_solved else "var(--text)"

            with col:
                st.markdown(
                    f'<div class="ch-card" style="background:{bg};border-color:{brd};color:{tc}">'
                    f'<div style="display:flex;align-items:flex-start;gap:8px">'
                    f'<span style="font-size:18px;line-height:1.2">{status_icon}</span>'
                    f'<div style="flex:1">'
                    f'<div style="font-weight:700;font-size:14px">{challenge["title"]}</div>'
                    f'<span class="diff-pill" style="background:{diff_color}22;'
                    f'color:{diff_color};border:1px solid {diff_color}55">{diff}</span>'
                    f'</div></div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Open  →", key=f"open_{cid}", use_container_width=True):
                    st.session_state["current_challenge_id"] = cid
                    st.session_state["coding_view"]          = "solver"
                    st.session_state["attempt_count"]        = 0
                    st.session_state["show_hint"]            = False
                    st.session_state["show_solution"]        = False
                    st.session_state["last_result"]          = None
                    st.session_state["test_results"]         = []
                    # Clear previous editor state so starter code reloads
                    st.session_state.pop(f"editor_{cid}", None)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 2 — CHALLENGE SOLVER
# ══════════════════════════════════════════════════════════════════════════════

def render_solver():
    cid       = st.session_state.get("current_challenge_id")
    challenge = find_challenge(cid) if cid else None

    if challenge is None:
        st.warning("Challenge not found. Returning to list.")
        st.session_state["coding_view"] = "list"
        st.rerun()
        return

    solved_ids    = set(st.session_state.progress.get("solved_coding", []))
    attempt_count = st.session_state.get("attempt_count", 0)
    last_result   = st.session_state.get("last_result")
    test_results  = st.session_state.get("test_results", [])
    test_cases    = build_test_cases(challenge)

    ch_num     = challenge["_ch_num"]
    diff       = challenge.get("difficulty", "Easy")
    diff_color = DIFF_COLOR.get(diff, "var(--subtext)")
    ch_idx     = challenge_index_in_chapter(cid)
    is_solved  = cid in solved_ids

    editor_key = f"editor_{cid}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = challenge.get("starter_code", "")

    # ── Back button ───────────────────────────────────────────────────────
    if st.button("← All challenges"):
        st.session_state["coding_view"] = "list"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Split layout ──────────────────────────────────────────────────────
    left_col, right_col = st.columns([2.2, 3])

    # ════════════════ LEFT PANEL ════════════════════════════════
    with left_col:
        st.markdown(
            f'<p style="font-family:ui-monospace,monospace;font-size:12px;color:var(--subtext)">'
            f'ch.{ch_num:02d} · challenge {ch_idx:02d} · '
            f'<span style="color:{diff_color}">{diff.lower()}</span></p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:24px;font-weight:700;line-height:1.25;margin-bottom:2px">'
            f'{challenge["title"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="scribble-line"></div>', unsafe_allow_html=True)

        # Description (preserve newlines)
        desc = challenge.get("description", "")
        st.markdown(
            f'<div style="color:var(--subtext);line-height:1.6;font-size:14px;margin-bottom:14px">'
            + desc.replace("\n", "<br>")
            + "</div>",
            unsafe_allow_html=True,
        )

        # Expected output
        expected = challenge.get("expected_output", "")
        st.markdown(
            f'<div class="output-box">'
            f'<div style="font-size:11px;color:var(--subtext);margin-bottom:6px">'
            f'expected output:</div>'
            + expected
            + "</div>",
            unsafe_allow_html=True,
        )

        # Hints
        hint_text = challenge.get("hint", "")
        if hint_text:
            hints = [h.strip() for h in hint_text.replace(";", "\n").splitlines() if h.strip()]
            hints_html = "".join(
                f'<div style="margin-bottom:4px">{i+1}. {h}</div>'
                for i, h in enumerate(hints)
            )
            st.markdown(
                f'<div class="info-box">'
                f'<div style="font-weight:700;margin-bottom:8px">💡 Hints</div>'
                f'<div style="font-size:13px;color:var(--subtext)">{hints_html}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Test cases
        if test_cases:
            tc_rows = ""
            for i, tc in enumerate(test_cases):
                if i < len(test_results):
                    icon       = "✓" if test_results[i] else "✗"
                    icon_color = "#27ae60" if test_results[i] else "#c0392b"
                else:
                    icon       = "○"
                    icon_color = "#888"
                label = tc.get("label", f"Test {i + 1}")
                tc_rows += (
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">'
                    f'<span style="font-weight:700;color:{icon_color};font-size:16px;'
                    f'font-family:ui-monospace,monospace">{icon}</span>'
                    f'<span style="font-size:13px">{label}</span>'
                    f'</div>'
                )
            st.markdown(
                f'<div class="test-box">'
                f'<div style="font-weight:700;margin-bottom:8px">🧪 Test cases ({len(test_cases)})</div>'
                f'{tc_rows}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Show Solution after 2+ failed attempts
        if attempt_count >= 2 and not is_solved:
            if st.button("👁️ Show Solution", key="show_sol_btn"):
                st.session_state["show_solution"] = not st.session_state.get("show_solution", False)
                st.rerun()
            if st.session_state.get("show_solution", False):
                st.code(challenge.get("solution", ""), language="python")

    # ════════════════ RIGHT PANEL ════════════════════════════════
    with right_col:
        # Toolbar
        tb_l, tb_r = st.columns([2, 3])
        with tb_l:
            st.markdown(
                '<div style="font-family:ui-monospace,monospace;font-size:13px;'
                'color:var(--subtext);padding-top:8px">solution.py</div>',
                unsafe_allow_html=True,
            )
        with tb_r:
            btn_reset, btn_hint, btn_run = st.columns(3)
            with btn_reset:
                if st.button("↺ Reset", key="reset_btn", use_container_width=True):
                    st.session_state[editor_key] = challenge.get("starter_code", "")
                    st.session_state["last_result"]  = None
                    st.session_state["test_results"] = []
                    st.rerun()
            with btn_hint:
                if st.button("💡 Hint", key="hint_btn", use_container_width=True):
                    st.session_state["show_hint"] = not st.session_state.get("show_hint", False)
                    st.rerun()
            with btn_run:
                run_pressed = st.button(
                    "▶ Run & test", key="run_btn", type="primary", use_container_width=True
                )

        # Inline hint strip
        if st.session_state.get("show_hint") and hint_text:
            hints = [h.strip() for h in hint_text.replace(";", "\n").splitlines() if h.strip()]
            st.markdown(
                f'<div style="background:#FFF8E0;border:1.5px solid #E09000;border-radius:8px;'
                f'padding:8px 12px;font-size:13px;color:#1a1a1a;margin-top:6px">'
                f'💡 {hints[0] if hints else hint_text}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Code editor
        current_code = st.text_area(
            "Code",
            value=st.session_state.get(editor_key, challenge.get("starter_code", "")),
            height=300,
            key=editor_key,
            label_visibility="collapsed",
        )

        # ── Run & test logic ──────────────────────────────────────────────
        if run_pressed:
            if not can_run_code():
                st.warning(
                    "**Code runner not available in demo mode.**  \n"
                    "Download the app and run it locally to practice coding. "
                    "See the README for instructions."
                )
            else:
                # Collect stdin_values from all test cases for this run
                all_stdin: list = []
                for tc in test_cases:
                    all_stdin.extend(tc.get("stdin_values", []))
                result = run_code(current_code, stdin_values=all_stdin or None)
                st.session_state["last_result"]  = result
                st.session_state["attempt_count"] += 1

                new_test_results = []
                for tc in test_cases:
                    expected_out = tc.get("expected_output", "").strip()
                    actual_out   = result.stdout.strip()
                    new_test_results.append(actual_out == expected_out)
                st.session_state["test_results"] = new_test_results

                all_passed = bool(new_test_results) and all(new_test_results)

                if all_passed and not result.timed_out and result.exit_code == 0:
                    p, xp_earned = prog_utils.mark_solved(st.session_state.progress, cid)
                    st.session_state.progress = p
                    st.session_state["solved_this_session"].add(cid)
                    if xp_earned == 25:
                        st.balloons()

                st.rerun()

        # ── Output panel ──────────────────────────────────────────────────
        last = st.session_state.get("last_result")
        if last is not None:
            all_passed    = bool(test_results) and all(test_results)
            passed_count  = sum(1 for r in test_results if r)
            total_tests   = len(test_results)

            if last.timed_out:
                status_html = (
                    '<span style="background:#c0392b;color:#fff;border-radius:999px;'
                    'padding:2px 10px;font-size:12px;font-weight:700">✗ timed out (10 s)</span>'
                )
            elif all_passed:
                n = total_tests
                status_html = (
                    f'<span style="background:#27ae60;color:#fff;border-radius:999px;'
                    f'padding:2px 10px;font-size:12px;font-weight:700">'
                    f'✓ all {n} test{"s" if n != 1 else ""} passed</span>'
                )
            else:
                failed = total_tests - passed_count
                status_html = (
                    f'<span style="background:#c0392b;color:#fff;border-radius:999px;'
                    f'padding:2px 10px;font-size:12px;font-weight:700">'
                    f'✗ {failed} failed</span>'
                )

            st.markdown(
                f'<div style="background:var(--surface);border:1.5px solid var(--border);'
                f'border-radius:10px;padding:10px 14px;margin-top:6px">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                f'<span style="font-weight:700;font-size:14px">Output</span>'
                f'{status_html}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            if last.stdout:
                st.code(last.stdout, language="text")
            elif not last.timed_out and last.exit_code == 0:
                st.caption("(no output)")

            if last.stderr:
                st.error(last.stderr)

            if last.timed_out:
                st.warning("Your code took longer than 10 seconds — check for infinite loops.")
            elif all_passed:
                attempts = st.session_state.get("attempt_count", 1)
                already_solved = is_solved and cid not in st.session_state.get("solved_this_session", set())
                xp_msg = "+5 XP practice bonus" if already_solved else "+25 XP"
                st.markdown(
                    f'<div style="background:#E6FFE6;border:1.5px solid #27ae60;border-radius:10px;'
                    f'padding:12px 16px;color:#1a1a1a;font-size:14px;margin-top:6px">'
                    f'Nice work — solved in {attempts} attempt{"s" if attempts != 1 else ""}. '
                    f'<b>{xp_msg}</b>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            elif attempt_count >= 2:
                st.markdown(
                    '<div style="color:var(--subtext);font-size:13px;margin-top:6px">'
                    'Still not passing? Check the hints on the left, or reveal the solution.'
                    '</div>',
                    unsafe_allow_html=True,
                )

        # ── AI debug button ───────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🤖 Ask AI to help me debug", key="ai_debug_btn", use_container_width=True):
            last = st.session_state.get("last_result")
            error_ctx = ""
            if last and last.stderr:
                error_ctx = f"\n\nError:\n{last.stderr}"
            elif last:
                error_ctx = (
                    f"\n\nMy output:\n{last.stdout.strip() or '(empty)'}"
                    f"\n\nExpected:\n{challenge.get('expected_output', '').strip()}"
                )
            st.session_state["ai_prefill"] = (
                f"I'm working on this Python challenge: '{challenge['title']}'.\n\n"
                f"Problem: {challenge.get('description', '')[:300]}\n\n"
                f"My code:\n```python\n{current_code}\n```"
                f"{error_ctx}\n\n"
                "Give me a hint to fix this — don't give the full solution, just a nudge."
            )
            st.switch_page("pages/04_ai_tutor.py")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

_view = st.session_state.get("coding_view", "list")

if _view == "solver":
    render_solver()
else:
    render_list()
