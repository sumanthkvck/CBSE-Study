"""
MCQ Practice page — IP Learn
Four views: setup → practice | timed → results
"""
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils import progress as prog_utils
from app.utils.css import inject_theme_css
from app.components.sidebar import render_sidebar

st.set_page_config(page_title="MCQ Practice — IP Learn", page_icon="✅", layout="wide")
st.session_state["_current_page"] = "mcq"

CONTENT_DIR = Path(__file__).parent.parent / "content"
TIMED_SECONDS = 600  # 10 minutes

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

OPTION_LETTERS = ["A", "B", "C", "D"]

# ── Bootstrap ─────────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = prog_utils.load()

render_sidebar(st.session_state.progress)
inject_theme_css(st.session_state.progress.get("theme", "Dark"))

# Pre-filter from another page (e.g., learn page passes a chapter number)
# Preset chapter filter from another page — may be int or list
_preset_chapters = st.session_state.pop("mcq_chapter_filter", None)
if isinstance(_preset_chapters, int):
    _preset_chapters = [_preset_chapters]

# Session state defaults
_defaults = {
    "mcq_view": "setup",
    "mcq_config": {
        "chapters": _preset_chapters if _preset_chapters else [1],
        "difficulty": "Mixed",
        "count": 10,
        "mode": "practice",
    },
    "quiz_questions": [],
    "quiz_current_idx": 0,
    "quiz_answers": {},
    "quiz_marked": [],
    "quiz_start_time": None,
    "mcq_results": [],
    "session_correct": 0,
    "session_total": 0,
    "quiz_xp_awarded": False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# If arriving with preset chapters, reset to setup view
if _preset_chapters is not None:
    st.session_state["mcq_view"] = "setup"
    st.session_state["mcq_config"]["chapters"] = _preset_chapters

# ── Extra CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* rounded pill buttons */
div[data-testid="column"] .stButton > button {
    border-radius: 8px;
}
/* Question card */
.mcq-qcard {
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 12px;
}
/* Answered option states */
.mcq-opt {
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--surface);
    margin-bottom: 4px;
}
.mcq-opt.correct {
    background: #E6FFE6;
    border-color: #27ae60;
    box-shadow: 3px 3px 0 #27ae60;
    color: #1a1a1a;
}
.mcq-opt.wrong {
    background: #FFE6E6;
    border-color: #c0392b;
    color: #1a1a1a;
}
.mcq-opt.neutral { background: var(--surface); }
.opt-badge {
    width: 28px; height: 28px; min-width: 28px;
    border: 1.5px solid var(--border);
    border-radius: 6px;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px;
    background: var(--card);
}
.opt-badge.correct { background: #27ae60; color: #fff; border-color: #27ae60; }
.opt-badge.wrong   { background: #c0392b; color: #fff; border-color: #c0392b; }
/* Breakdown table */
.breakdown-wrap {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 16px;
}
.breakdown-hdr {
    padding: 12px 16px;
    border-bottom: 1.5px solid var(--border);
    font-weight: 700;
    background: var(--card);
}
.breakdown-row {
    display: grid;
    grid-template-columns: 36px 1.5fr 90px 90px 1fr;
    gap: 10px;
    align-items: center;
    padding: 10px 16px;
    border-bottom: 1px dashed var(--border);
    font-size: 14px;
}
.breakdown-row:last-child { border-bottom: none; }
</style>
""", unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────────────────

@st.cache_data
def load_chapter_mcqs(filename: str) -> list:
    path = CONTENT_DIR / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("mcqs", [])
    except Exception:
        return []


def load_questions(chapter_nums: list, difficulty: str, count: int) -> list:
    all_q = []
    for ch in CHAPTERS:
        if ch["num"] in chapter_nums:
            for q in load_chapter_mcqs(ch["file"]):
                q = dict(q)
                q["chapter_num"] = ch["num"]
                q["chapter_title"] = ch["title"]
                all_q.append(q)
    if difficulty != "Mixed":
        all_q = [q for q in all_q if q.get("difficulty", "").lower() == difficulty.lower()]
    random.shuffle(all_q)
    return all_q[:count]


def elapsed_secs() -> int:
    t = st.session_state.get("quiz_start_time")
    if t is None:
        return 0
    return int((datetime.now() - t).total_seconds())


def remaining_secs() -> int:
    return max(0, TIMED_SECONDS - elapsed_secs())


def fmt_time(sec: int) -> str:
    m, s = divmod(abs(sec), 60)
    return f"{m:02d}:{s:02d}"


def start_quiz() -> bool:
    cfg = st.session_state["mcq_config"]
    qs = load_questions(cfg["chapters"], cfg["difficulty"], cfg["count"])
    if not qs:
        st.warning("No questions found for that combination. Try a different difficulty or chapter.")
        return False
    st.session_state["quiz_questions"] = qs
    st.session_state["quiz_current_idx"] = 0
    st.session_state["quiz_answers"] = {}
    st.session_state["quiz_marked"] = []
    st.session_state["quiz_start_time"] = datetime.now()
    st.session_state["quiz_xp_awarded"] = False
    st.session_state["session_correct"] = 0
    st.session_state["session_total"] = 0
    return True


def compute_results() -> list:
    questions = st.session_state.get("quiz_questions", [])
    answers = st.session_state.get("quiz_answers", {})
    results = []
    for i, q in enumerate(questions):
        sel = answers.get(i)
        skipped = sel is None
        correct = (not skipped) and (sel == q["correct_index"])
        results.append({
            "q_num": i + 1,
            "question": q["question"],
            "options": q["options"],
            "selected_idx": sel,
            "correct_idx": q["correct_index"],
            "skipped": skipped,
            "correct": correct,
            "difficulty": q.get("difficulty", "Medium"),
            "explanation": q.get("explanation", ""),
            "chapter_num": q.get("chapter_num", 1),
        })
    return results


def _pill_row(options, current, key_prefix, on_select):
    """Render a horizontal row of pill buttons; primary style = selected."""
    cols = st.columns(len(options))
    for i, opt in enumerate(options):
        btn_type = "primary" if str(current) == str(opt) else "secondary"
        if cols[i].button(str(opt), key=f"{key_prefix}_{opt}", type=btn_type, use_container_width=True):
            on_select(opt)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — SETUP
# ══════════════════════════════════════════════════════════════════════════════

def render_setup():
    st.markdown("## Start a quiz")
    st.markdown(
        '<p style="color:var(--subtext);margin-top:-8px;margin-bottom:18px">Pick scope, length and difficulty</p>',
        unsafe_allow_html=True,
    )

    cfg = st.session_state["mcq_config"]
    col_left, col_right = st.columns([1.4, 1])

    # ── LEFT: configuration ───────────────────────────────────────────────
    with col_left:
        with st.container(border=True):
            # Chapter scope
            st.markdown("**Chapter scope**")
            ch_cols = st.columns(2)
            new_selected = []
            for i, ch in enumerate(CHAPTERS):
                col = ch_cols[i % 2]
                default_on = ch["num"] in cfg["chapters"]
                checked = col.checkbox(
                    f"Ch.{ch['num']:02d}: {ch['title']}",
                    value=default_on,
                    key=f"chk_ch{ch['num']}",
                )
                if checked:
                    new_selected.append(ch["num"])
            cfg["chapters"] = new_selected

            st.markdown("---")

            # Difficulty pills
            st.markdown("**Difficulty**")
            _pill_row(
                ["Easy", "Medium", "Hard", "Mixed"],
                cfg["difficulty"],
                "diff",
                lambda v: cfg.update({"difficulty": v}),
            )

            st.markdown("---")

            # Count pills
            st.markdown("**Number of questions**")
            _pill_row(
                [5, 10, 15, 25],
                cfg["count"],
                "cnt",
                lambda v: cfg.update({"count": v}),
            )

            st.markdown("---")

            # Mode cards
            st.markdown("**Mode**")
            mc1, mc2 = st.columns(2)

            practice_bg  = "var(--surface)" if cfg["mode"] == "practice" else "var(--card)"
            practice_brd = "2px solid var(--accent)" if cfg["mode"] == "practice" else "1.5px solid var(--border)"
            timed_bg     = "#FFF8E0" if cfg["mode"] == "timed" else "var(--card)"
            timed_brd    = "2.5px solid #E09000" if cfg["mode"] == "timed" else "1.5px solid var(--border)"
            timed_tc     = "#1a1a1a" if cfg["mode"] == "timed" else "var(--text)"

            with mc1:
                st.markdown(
                    f'<div style="background:{practice_bg};border:{practice_brd};border-radius:10px;'
                    f'padding:12px 14px;min-height:68px">'
                    f'<b>Practice</b>'
                    f'<div style="color:var(--subtext);font-size:13px;margin-top:4px">No timer · explanations after each Q</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Select Practice", key="mode_practice", use_container_width=True,
                             type="primary" if cfg["mode"] == "practice" else "secondary"):
                    cfg["mode"] = "practice"
                    st.rerun()

            with mc2:
                st.markdown(
                    f'<div style="background:{timed_bg};border:{timed_brd};border-radius:10px;'
                    f'padding:12px 14px;min-height:68px;color:{timed_tc}">'
                    f'<b>Timed mock</b>'
                    f'<div style="color:#666;font-size:13px;margin-top:4px">10 min · results at end · feels like an exam</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Select Timed", key="mode_timed", use_container_width=True,
                             type="primary" if cfg["mode"] == "timed" else "secondary"):
                    cfg["mode"] = "timed"
                    st.rerun()

    # ── RIGHT: summary + start ────────────────────────────────────────────
    with col_right:
        ch_label = (
            f"Ch.{cfg['chapters'][0]:02d}" if len(cfg["chapters"]) == 1
            else f"{len(cfg['chapters'])} chapters" if cfg["chapters"]
            else "No chapters"
        )
        mode_label = "Timed" if cfg["mode"] == "timed" else "Practice"
        xp_per    = 5 if cfg["mode"] == "timed" else 10
        time_lim  = "10:00" if cfg["mode"] == "timed" else "No limit"

        with st.container(border=True):
            st.markdown(
                '<p style="font-family:ui-monospace,monospace;font-size:12px;color:var(--subtext)">your quiz</p>',
                unsafe_allow_html=True,
            )
            st.markdown(f"### {ch_label} · {cfg['count']} Qs · {cfg['difficulty']} · {mode_label}")
            st.divider()
            st.markdown(f"**Time limit** — `{time_lim}`")
            st.markdown(f"**Reward per correct** — `+{xp_per} XP`")
            st.markdown("**Penalty for wrong** — `0 XP`")
            best = st.session_state.progress.get("mcq_best", {}).get(
                "_".join(str(n) for n in sorted(cfg["chapters"])), None
            )
            st.markdown(f"**Best previous score** — `{best if best else '—'}`")
            st.divider()

            if st.button("▶  Start quiz", type="primary", use_container_width=True):
                if not cfg["chapters"]:
                    st.warning("Select at least one chapter.")
                elif start_quiz():
                    st.session_state["mcq_view"] = cfg["mode"]
                    st.rerun()

        st.markdown(
            '<div style="background:var(--card);border:1.5px solid var(--border);border-radius:10px;'
            'padding:14px;margin-top:10px">'
            '<b>💡 Tip</b>'
            '<div style="color:var(--subtext);font-size:13px;margin-top:4px">'
            'Use "Mark for review" during the quiz — you can come back to flagged questions before submitting.'
            '</div></div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 2a — PRACTICE MODE
# ══════════════════════════════════════════════════════════════════════════════

def render_practice():
    questions = st.session_state.get("quiz_questions", [])
    if not questions:
        st.session_state["mcq_view"] = "setup"
        st.rerun()
        return

    idx      = st.session_state["quiz_current_idx"]
    answers  = st.session_state["quiz_answers"]
    cfg      = st.session_state["mcq_config"]
    total    = len(questions)

    # All questions answered — go to results
    if idx >= total:
        st.session_state["mcq_results"] = compute_results()
        st.session_state["mcq_view"] = "results"
        st.rerun()
        return

    q        = questions[idx]
    answered = idx in answers
    selected = answers.get(idx)

    # Answered/wrong counts up to current question
    correct_so_far = sum(
        1 for i, q2 in enumerate(questions[:idx])
        if answers.get(i) == q2["correct_index"]
    )
    wrong_so_far = sum(
        1 for i in range(idx)
        if i in answers and answers[i] != questions[i]["correct_index"]
    )

    # ── Header ────────────────────────────────────────────────────────────
    h_left, h_right = st.columns([3, 1])
    with h_left:
        st.markdown(
            '<p style="font-family:ui-monospace,monospace;font-size:13px;color:var(--subtext)">// practice</p>',
            unsafe_allow_html=True,
        )
        st.markdown("## MCQ Practice")
    with h_right:
        ch_nums  = sorted(cfg["chapters"])
        ch_lbl   = ", ".join(f"Ch.{n:02d}" for n in ch_nums[:2]) + ("…" if len(ch_nums) > 2 else "")
        diff_lbl = cfg["difficulty"]
        st.markdown(
            f'<div style="margin-top:28px;text-align:right">'
            f'<span style="border:1.5px solid var(--border);border-radius:999px;'
            f'padding:4px 12px;font-size:12px;font-weight:600;margin-right:6px">{ch_lbl}</span>'
            f'<span style="border:1.5px solid var(--border);border-radius:999px;'
            f'padding:4px 12px;font-size:12px;font-weight:600">{diff_lbl}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Progress strip ────────────────────────────────────────────────────
    pct = int(idx / total * 100)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px">'
        f'<span style="font-family:ui-monospace,monospace;font-size:13px;'
        f'color:var(--subtext);white-space:nowrap">Q {idx+1} / {total}</span>'
        f'<div style="flex:1;height:10px;border:1.5px solid var(--border);'
        f'border-radius:999px;background:var(--card);overflow:hidden">'
        f'<div style="width:{pct}%;height:100%;background:var(--accent);border-radius:999px"></div>'
        f'</div>'
        f'<span style="font-size:13px;white-space:nowrap">{correct_so_far} ✅ · {wrong_so_far} ❌</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Question card ─────────────────────────────────────────────────────
    diff = q.get("difficulty", "Medium")
    diff_color = {"Easy": "#27ae60", "Medium": "#e67e22", "Hard": "#c0392b"}.get(diff, "var(--subtext)")
    st.markdown(
        f'<div class="mcq-qcard">'
        f'<div style="font-family:ui-monospace,monospace;font-size:13px;color:var(--subtext)">'
        f'question {idx+1:02d} · <span style="color:{diff_color}">{diff.lower()}</span></div>'
        f'<div style="font-size:21px;font-weight:700;margin-top:8px;line-height:1.4">{q["question"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Options ───────────────────────────────────────────────────────────
    if answered:
        # Static HTML — show correct/wrong coloring
        left_opts, right_opts = q["options"][:2], q["options"][2:]
        html_rows = []
        for j, opt_text in enumerate(q["options"]):
            is_correct  = j == q["correct_index"]
            is_selected = j == selected
            if is_correct:
                cls        = "correct"
                badge_cls  = "correct"
                suffix     = '<span style="margin-left:auto;color:#27ae60;font-weight:600;font-size:13px">✓ correct</span>'
            elif is_selected:
                cls        = "wrong"
                badge_cls  = "wrong"
                suffix     = '<span style="margin-left:auto;color:#c0392b;font-size:13px">✗ wrong</span>'
            else:
                cls        = "neutral"
                badge_cls  = ""
                suffix     = ""
            html_rows.append(
                f'<div class="mcq-opt {cls}">'
                f'<div class="opt-badge {badge_cls}">{OPTION_LETTERS[j]}</div>'
                f'<div style="font-size:15px;flex:1">{opt_text}</div>'
                f'{suffix}'
                f'</div>'
            )
        # 2-col grid layout
        st.markdown(
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">'
            + "".join(html_rows)
            + "</div>",
            unsafe_allow_html=True,
        )
    else:
        # Interactive buttons in 2×2 grid
        oc1, oc2 = st.columns(2)
        for j, opt_text in enumerate(q["options"]):
            target_col = oc1 if j % 2 == 0 else oc2
            with target_col:
                if st.button(
                    f"{OPTION_LETTERS[j]}.  {opt_text}",
                    key=f"opt_{idx}_{j}",
                    use_container_width=True,
                ):
                    st.session_state["quiz_answers"][idx] = j
                    st.rerun()

    # ── Explanation box ───────────────────────────────────────────────────
    if answered:
        is_right = selected == q["correct_index"]
        if is_right:
            box_bg   = "#E6FFE6"
            box_brd  = "#27ae60"
            headline = "Nice — that's right! +10 XP 🎉"
        else:
            box_bg   = "#FFE6E6"
            box_brd  = "#c0392b"
            cl       = OPTION_LETTERS[q["correct_index"]]
            headline = f"Wrong. Correct answer was {cl}."

        st.markdown(
            f'<div style="background:{box_bg};border:1.5px solid {box_brd};border-radius:10px;'
            f'padding:14px 16px;margin-bottom:12px;color:#1a1a1a">'
            f'<b>{headline}</b>'
            f'<div style="margin-top:6px;color:#555;font-size:14px">{q.get("explanation", "")}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Award XP for correct (+10 in practice mode), once per question
        if is_right:
            xp_key = f"xp_q{idx}_awarded"
            if xp_key not in st.session_state:
                st.session_state.progress = prog_utils.add_xp(
                    st.session_state.progress, 10
                )
                st.session_state[xp_key] = True

    # ── Action row ────────────────────────────────────────────────────────
    act_l, act_m, _, act_r = st.columns([1.2, 1, 0.5, 1.5])

    with act_l:
        if st.button("🤖 Explain with AI", key=f"ai_{idx}", use_container_width=True):
            st.session_state["ai_prefill"] = (
                f"Explain this MCQ question to me:\n\n{q['question']}\n\n"
                + "\n".join(f"{OPTION_LETTERS[j]}. {o}" for j, o in enumerate(q["options"]))
            )
            st.switch_page("pages/04_ai_tutor.py")

    with act_m:
        if not answered:
            if st.button("Skip", key=f"skip_{idx}", use_container_width=True):
                st.session_state["quiz_current_idx"] += 1
                st.rerun()

    with act_r:
        if answered:
            is_last = idx + 1 >= total
            next_lbl = "Finish quiz  →" if is_last else "Next question  →"
            if st.button(next_lbl, key=f"next_{idx}", type="primary", use_container_width=True):
                if is_last:
                    st.session_state["mcq_results"] = compute_results()
                    st.session_state["mcq_view"] = "results"
                else:
                    st.session_state["quiz_current_idx"] += 1
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 2b — TIMED MODE
# ══════════════════════════════════════════════════════════════════════════════

def render_timed():
    questions = st.session_state.get("quiz_questions", [])
    if not questions:
        st.session_state["mcq_view"] = "setup"
        st.rerun()
        return

    idx     = st.session_state["quiz_current_idx"]
    answers = st.session_state["quiz_answers"]
    marked  = st.session_state["quiz_marked"]
    cfg     = st.session_state["mcq_config"]
    total   = len(questions)
    secs    = remaining_secs()

    # Auto-submit on time-out or when navigated past last question
    if secs == 0 or idx >= total:
        st.session_state["mcq_results"] = compute_results()
        st.session_state["mcq_view"] = "results"
        st.rerun()
        return

    q = questions[min(idx, total - 1)]

    # ── Header row: title + timer ─────────────────────────────────────────
    hdr_l, hdr_r = st.columns([3, 1])
    with hdr_l:
        ch_nums = sorted(cfg["chapters"])
        ch_lbl  = ", ".join(f"ch.{n:02d}" for n in ch_nums[:2]) + ("…" if len(ch_nums) > 2 else "")
        st.markdown(
            f'<p style="font-family:ui-monospace,monospace;font-size:12px;color:var(--subtext)">'
            f'// timed quiz · {ch_lbl}</p>',
            unsafe_allow_html=True,
        )
        st.markdown("### Chapter mock test")
    with hdr_r:
        warn_color = "#c0392b" if secs < 60 else "#E09000"
        st.markdown(
            f'<div style="background:#FFF0E0;border:2px solid {warn_color};border-radius:10px;'
            f'padding:10px 18px;text-align:center;margin-top:10px">'
            f'<div style="font-size:12px;color:#666;font-family:ui-monospace,monospace">time left</div>'
            f'<div style="font-size:28px;font-weight:700;font-family:ui-monospace,monospace;color:#1a1a1a">'
            f'{fmt_time(secs)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Question pager (HTML, visual only) ────────────────────────────────
    pager_html = '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px">'
    for i in range(total):
        is_cur  = i == idx
        is_ans  = i in answers
        is_mark = i in marked
        if is_cur:
            bg, tc = "var(--accent)", "#fff"
        elif is_ans:
            bg, tc = "#27ae60", "#fff"
        elif is_mark:
            bg, tc = "var(--warn)", "#fff"
        else:
            bg, tc = "var(--card)", "var(--text)"
        pager_html += (
            f'<div style="width:32px;height:32px;border:1.5px solid var(--border);border-radius:6px;'
            f'display:flex;align-items:center;justify-content:center;background:{bg};color:{tc};'
            f'font-size:13px;font-weight:700">{i + 1}</div>'
        )
    pager_html += "</div>"
    st.markdown(pager_html, unsafe_allow_html=True)

    # ── Two-column layout ─────────────────────────────────────────────────
    q_col, info_col = st.columns([1.7, 1])

    with q_col:
        diff       = q.get("difficulty", "Medium")
        diff_color = {"Easy": "#27ae60", "Medium": "#e67e22", "Hard": "#c0392b"}.get(diff, "var(--subtext)")

        st.markdown(
            f'<div style="background:var(--surface);border:1.5px solid var(--border);'
            f'border-radius:12px;padding:20px;margin-bottom:12px">'
            f'<div style="font-size:12px;color:var(--subtext);font-family:ui-monospace,monospace">'
            f'Question {idx + 1} / {total} · <span style="color:{diff_color}">{diff}</span></div>'
            f'<div style="font-size:20px;font-weight:700;margin-top:8px;line-height:1.4">{q["question"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Vertical radio-style options
        cur_sel = answers.get(idx)
        for j, opt_text in enumerate(q["options"]):
            is_sel     = cur_sel == j
            sel_bg     = "var(--card)"   if is_sel else "var(--surface)"
            sel_brd    = "var(--accent)" if is_sel else "var(--border)"
            radio_fill = "var(--accent)" if is_sel else "transparent"
            st.markdown(
                f'<div style="display:flex;gap:10px;align-items:center;padding:10px 12px;'
                f'border:1.5px solid {sel_brd};border-radius:8px;background:{sel_bg};'
                f'font-family:ui-monospace,monospace;margin-bottom:4px">'
                f'<span style="width:18px;height:18px;border:1.5px solid var(--border);'
                f'border-radius:50%;background:{radio_fill};display:inline-block"></span>'
                f'<b>{OPTION_LETTERS[j]}.</b> {opt_text}'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                f"Select {OPTION_LETTERS[j]}",
                key=f"topt_{idx}_{j}",
                use_container_width=True,
            ):
                st.session_state["quiz_answers"][idx] = j
                st.rerun()

        # Navigation buttons
        nav_l, nav_m, nav_r = st.columns([1, 1, 1])
        with nav_l:
            if st.button("← Previous", key=f"prev_{idx}", use_container_width=True, disabled=idx == 0):
                st.session_state["quiz_current_idx"] -= 1
                st.rerun()
        with nav_m:
            is_marked_now = idx in marked
            mark_lbl = "✅ Unmark" if is_marked_now else "🚩 Mark for review"
            if st.button(mark_lbl, key=f"mark_{idx}", use_container_width=True):
                if is_marked_now:
                    st.session_state["quiz_marked"].remove(idx)
                else:
                    st.session_state["quiz_marked"].append(idx)
                st.rerun()
        with nav_r:
            is_last  = idx + 1 >= total
            next_lbl = "Submit  →" if is_last else "Save & Next  →"
            if st.button(next_lbl, key=f"tnext_{idx}", type="primary", use_container_width=True):
                if is_last:
                    st.session_state["mcq_results"] = compute_results()
                    st.session_state["mcq_view"] = "results"
                else:
                    st.session_state["quiz_current_idx"] += 1
                st.rerun()

    with info_col:
        answered_count = len(answers)
        marked_count   = len(marked)
        todo_count     = total - answered_count - marked_count

        st.markdown(
            f'<div style="background:var(--surface);border:1.5px solid var(--border);'
            f'border-radius:12px;padding:14px;margin-bottom:12px">'
            f'<div style="font-weight:700;margin-bottom:8px">Legend</div>'
            + "".join(
                f'<div style="display:flex;align-items:center;gap:8px;margin-top:6px">'
                f'<span style="width:16px;height:16px;border:1.5px solid var(--border);'
                f'background:{bg};border-radius:4px;display:inline-block;flex-shrink:0"></span>'
                f'<span style="flex:1">{label}</span>'
                f'<span style="color:var(--subtext)">{count}</span></div>'
                for label, bg, count in [
                    ("Answered", "#27ae60", answered_count),
                    ("Marked",   "var(--warn)", marked_count),
                    ("Current",  "var(--accent)", 1),
                    ("Not yet",  "var(--card)", todo_count),
                ]
            )
            + '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="background:var(--card);border:1.5px solid var(--border);'
            f'border-radius:12px;padding:14px;margin-bottom:12px">'
            f'<div style="font-weight:700">About this quiz</div>'
            f'<div style="color:var(--subtext);font-size:13px;margin-top:4px">'
            f'{total} questions · 10 min · +5 XP per correct · −0 for wrong</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.button("End quiz early", key="end_early", use_container_width=True):
            st.session_state["mcq_results"] = compute_results()
            st.session_state["mcq_view"] = "results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════

def render_results():
    results = st.session_state.get("mcq_results", [])
    if not results:
        st.session_state["mcq_view"] = "setup"
        st.rerun()
        return

    cfg     = st.session_state["mcq_config"]
    total   = len(results)
    correct = sum(1 for r in results if r["correct"])
    wrong   = sum(1 for r in results if not r["correct"] and not r["skipped"])
    skipped = sum(1 for r in results if r["skipped"])
    pct     = int(correct / total * 100) if total else 0
    mode_lbl = "timed mock" if cfg["mode"] == "timed" else "practice"
    xp_per   = 5 if cfg["mode"] == "timed" else 10
    xp_total = correct * xp_per

    # Award XP and record MCQ stats exactly once
    if not st.session_state.get("quiz_xp_awarded", False):
        p2 = st.session_state.progress
        p2 = prog_utils.add_xp(p2, xp_total)
        p2["mcq_correct"] = p2.get("mcq_correct", 0) + correct
        p2["mcq_total"]   = p2.get("mcq_total",   0) + total
        # Save best score keyed by sorted chapter list
        score_key = "_".join(str(n) for n in sorted(cfg["chapters"]))
        prev_best = p2.get("mcq_best", {}).get(score_key, 0)
        if correct > prev_best:
            p2.setdefault("mcq_best", {})[score_key] = correct
        prog_utils.save(p2)
        st.session_state.progress = p2
        st.session_state["quiz_xp_awarded"] = True

    elapsed = elapsed_secs()
    time_str = fmt_time(min(elapsed, TIMED_SECONDS))

    # Kicker
    ch_nums = sorted(cfg["chapters"])
    ch_lbl  = f"ch.{ch_nums[0]:02d}" if len(ch_nums) == 1 else f"{len(ch_nums)} chapters"
    st.markdown(
        f'<p style="font-family:ui-monospace,monospace;font-size:13px;color:var(--subtext)">'
        f'// {ch_lbl} · {total} questions · {mode_lbl}</p>',
        unsafe_allow_html=True,
    )

    # ── Hero row ──────────────────────────────────────────────────────────
    name     = st.session_state.progress.get("name", "").strip() or "Student"
    congrats = (
        "Perfect score! 🏆" if pct == 100 else
        f"Great work, {name}! 🎉" if pct >= 70 else
        f"Keep practising, {name}! 💪"
    )
    hero_l, hero_r = st.columns([1, 4])
    with hero_l:
        st.markdown(
            f'<div style="width:120px;height:120px;border-radius:50%;border:2px solid var(--border);'
            f'background:#E6FFE6;display:flex;flex-direction:column;align-items:center;'
            f'justify-content:center;box-shadow:4px 4px 0 var(--border);text-align:center">'
            f'<div style="font-size:26px;font-weight:700;color:#1a1a1a;line-height:1">{correct}/{total}</div>'
            f'<div style="font-size:12px;color:#555;margin-top:2px">{pct}% accuracy</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with hero_r:
        st.markdown(f"## {congrats}")
        st.markdown(
            f'<div style="color:var(--subtext);margin-top:-8px">'
            f'<b style="color:#27ae60">+{xp_total} XP</b> earned · {correct} out of {total} correct'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 4-metric row ─────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    for col, label, value, color in [
        (m1, "Correct",   str(correct), "#27ae60"),
        (m2, "Wrong",     str(wrong),   "#c0392b"),
        (m3, "Skipped",   str(skipped), "var(--warn)"),
        (m4, "Time used", time_str,     "var(--text)"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:var(--surface);border:1.5px solid var(--border);'
                f'border-radius:12px;padding:16px">'
                f'<div style="font-size:13px;color:var(--subtext)">{label}</div>'
                f'<div style="font-size:26px;font-weight:700;color:{color}">{value}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Question breakdown ────────────────────────────────────────────────
    rows_html = ""
    for r in results:
        s = "correct" if r["correct"] else ("skipped" if r["skipped"] else "wrong")
        ic_bg  = {"correct": "#27ae60", "wrong": "#c0392b", "skipped": "var(--warn)"}[s]
        ic     = {"correct": "✓",       "wrong": "✗",       "skipped": "○"}[s]
        diff   = r.get("difficulty", "Medium")
        d_col  = {"Easy": "#27ae60", "Medium": "#e67e22", "Hard": "#c0392b"}.get(diff, "var(--subtext)")
        note   = ""
        if s == "wrong" and r["selected_idx"] is not None:
            note = f'You picked {OPTION_LETTERS[r["selected_idx"]]} · answer was {OPTION_LETTERS[r["correct_idx"]]}'
        q_short = (r["question"][:68] + "…") if len(r["question"]) > 68 else r["question"]
        rows_html += (
            f'<div class="breakdown-row">'
            f'<div style="width:26px;height:26px;border:1.5px solid var(--border);border-radius:6px;'
            f'background:{ic_bg};color:#fff;font-weight:700;font-size:14px;display:flex;'
            f'align-items:center;justify-content:center">{ic}</div>'
            f'<div><div style="font-size:11px;color:var(--subtext);font-family:ui-monospace,monospace">Q{r["q_num"]}</div>'
            f'<div>{q_short}</div></div>'
            f'<div><span style="border:1.5px solid {d_col};border-radius:999px;padding:2px 8px;'
            f'font-size:11px;color:{d_col}">{diff}</span></div>'
            f'<div style="color:{ic_bg};font-weight:700;text-transform:capitalize">{s}</div>'
            f'<div style="font-size:12px;color:var(--subtext)">{note}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="breakdown-wrap">'
        f'<div class="breakdown-hdr">Question breakdown · click to review</div>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Action row ────────────────────────────────────────────────────────
    a1, a2, a3, a4 = st.columns([2, 1.2, 1, 1.2])

    with a1:
        if st.button("🤖 AI: explain my mistakes", use_container_width=True):
            mistakes = [r for r in results if not r["correct"] and not r["skipped"]]
            if mistakes:
                q_texts = "; ".join(r["question"][:50] for r in mistakes[:5])
                st.session_state["ai_prefill"] = (
                    f"Explain why I got these MCQ questions wrong: {q_texts}"
                )
            st.switch_page("pages/04_ai_tutor.py")

    with a2:
        wrong_qs = [
            dict(st.session_state["quiz_questions"][i])
            for i, r in enumerate(results)
            if not r["correct"] and not r["skipped"]
            and i < len(st.session_state.get("quiz_questions", []))
        ]
        if st.button("Review wrong only", use_container_width=True):
            if wrong_qs:
                st.session_state["quiz_questions"]   = wrong_qs
                st.session_state["quiz_current_idx"] = 0
                st.session_state["quiz_answers"]     = {}
                st.session_state["quiz_marked"]      = []
                st.session_state["quiz_xp_awarded"]  = False
                st.session_state["mcq_view"]         = "practice"
                st.rerun()
            else:
                st.toast("No wrong answers to review!")

    with a3:
        if st.button("↺ Retake", use_container_width=True):
            st.session_state["mcq_results"] = []
            st.session_state["mcq_view"]    = "setup"
            st.rerun()

    with a4:
        if st.button("Next chapter  →", type="primary", use_container_width=True):
            st.switch_page("pages/01_learn.py")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

_view = st.session_state.get("mcq_view", "setup")

if _view == "setup":
    render_setup()
elif _view == "practice":
    render_practice()
elif _view == "timed":
    render_timed()
elif _view == "results":
    render_results()
else:
    st.session_state["mcq_view"] = "setup"
    st.rerun()
