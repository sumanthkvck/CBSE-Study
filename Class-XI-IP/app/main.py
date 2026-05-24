"""
IP Learn — Main Entry Point & Dashboard
Run with: streamlit run app/main.py
"""
import streamlit as st
import json
import traceback
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils import progress as prog_utils
from app.utils.css import inject_theme_css
from app.utils.themes import get_theme
from app.components.sidebar import render_sidebar
from app.utils.env import is_cloud, CLOUD_BANNER
from app.utils.errors import log_error

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.session_state["_current_page"] = "dashboard"
st.set_page_config(
    page_title="IP Learn — Class XI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load progress ─────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = prog_utils.load()

p = st.session_state.progress

# ── Sidebar + CSS ─────────────────────────────────────────────────────────────
render_sidebar(p)
inject_theme_css(p.get("theme", "Dark"))

t = get_theme(p.get("theme", "Dark"))
SURFACE = t["surface"]; BORDER = t["border"]; ACCENT = t["accent"]
SUCCESS = t["success"]; MUTED = t["subtext"]; TEXT = t["text"]
CARD = t["card"]; WARN = t.get("warn", "#FFC107")

if is_cloud():
    st.info(CLOUD_BANNER)

# ── Load chapter metadata (cached) ────────────────────────────────────────────
@st.cache_data
def load_chapter_counts(content_dir_str: str) -> dict:
    """Return {ch_num: {topics, mcqs, challenges}} for all 8 chapters."""
    content_dir = Path(content_dir_str)
    index = json.loads((content_dir / "index.json").read_text(encoding="utf-8"))
    counts = {}
    for ch in index["chapters"]:
        try:
            data = json.loads((content_dir / ch["file"]).read_text(encoding="utf-8"))
            counts[ch["num"]] = {
                "topics":     len(data.get("topics", [])),
                "mcqs":       len(data.get("mcqs", [])),
                "challenges": len(data.get("coding_challenges", [])),
            }
        except Exception:
            counts[ch["num"]] = {"topics": 0, "mcqs": 0, "challenges": 0}
    return counts

content_dir   = Path(__file__).parent / "content"
chapter_index = json.loads((content_dir / "index.json").read_text(encoding="utf-8"))
chapters      = chapter_index.get("chapters", [])
ch_counts     = load_chapter_counts(str(content_dir))

try:
    # ── Data helpers ──────────────────────────────────────────────────────────
    name             = p.get("name", "Student") or "Student"
    visited          = p.get("chapters_visited", [])
    chapter_progress = p.get("chapter_progress", {})
    today_str        = datetime.now().strftime("%Y-%m-%d")
    today_display    = datetime.now().strftime("%a, %d %b")
    daily_xp_today   = p.get("daily_xp", {}).get(today_str, 0)
    daily_goal       = p.get("daily_xp_goal", 50)
    xp               = p.get("xp", 0)
    streak           = p.get("streak", 0)
    mcq_correct      = p.get("mcq_correct", 0)
    mcq_total        = p.get("mcq_total", 0)
    accuracy         = int(mcq_correct / mcq_total * 100) if mcq_total >= 5 else None
    chapters_started = sum(1 for ch in chapters if ch["num"] in visited)

    def is_unlocked(num: int) -> bool:
        if num <= 4:
            return True
        return (num - 1) in visited

    def ch_status(ch: dict) -> str:
        num = ch["num"]
        if not is_unlocked(num):
            return "lock"
        pct = int(chapter_progress.get(str(num), 0))
        if pct >= 100:
            return "done"
        if num in visited:
            return "doing"
        return "todo"

    # ── Header row ────────────────────────────────────────────────────────────
    hdr_l, hdr_r = st.columns([4, 1])
    with hdr_l:
        st.markdown(
            f'<h1 style="margin:0 0 2px 0;font-size:30px">Your dashboard</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="color:{MUTED};margin:0 0 18px 0">Welcome back, {name} 👋 — small daily wins build streaks.</p>',
            unsafe_allow_html=True,
        )
    with hdr_r:
        st.markdown(
            f'<div style="text-align:right;padding-top:8px">'
            f'<span style="background:{SURFACE};border:1.5px solid {BORDER};'
            f'border-radius:999px;padding:4px 12px;font-size:13px;color:{MUTED}">📅 {today_display}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Stats row — 4 metric cards ────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)

    def stat_card(col, label: str, value: str, sub: str, sub_color: str):
        col.markdown(
            f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
            f'border-radius:12px;padding:16px 18px">'
            f'<div style="font-size:12px;color:{MUTED};font-family:ui-monospace,monospace;'
            f'margin-bottom:4px">{label}</div>'
            f'<div style="font-size:28px;font-weight:700;color:{TEXT}">{value}</div>'
            f'<div style="font-size:12px;color:{sub_color};margin-top:2px">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    xp_sub_color  = SUCCESS if daily_xp_today > 0 else MUTED
    xp_sub        = f"+{daily_xp_today} today" if daily_xp_today > 0 else "start earning XP!"
    streak_sub    = "🎉 keep it up!" if streak >= 7 else ("great start!" if streak > 0 else "start a streak today")
    ch_sub_color  = ACCENT if chapters_started > 0 else MUTED
    acc_val       = f"{accuracy}%" if accuracy is not None else "—"
    acc_sub       = f"last {mcq_total} MCQs" if mcq_total >= 5 else "answer 5+ MCQs to see"
    acc_color     = SUCCESS if accuracy and accuracy >= 80 else WARN if accuracy else MUTED

    stat_card(s1, "Total XP",     f"{xp:,}",              xp_sub,               xp_sub_color)
    stat_card(s2, "Streak",       f"{streak} days",        streak_sub,           ACCENT if streak >= 3 else MUTED)
    stat_card(s3, "Chapters",     f"{chapters_started}/8", "in progress",        ch_sub_color)
    stat_card(s4, "MCQ accuracy", acc_val,                 acc_sub,              acc_color)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Chapter list section ──────────────────────────────────────────────────
    filter_col, _ = st.columns([3, 2])
    with filter_col:
        ch_filter = st.radio(
            "Filter chapters",
            ["All", "In progress", "Done", "Not started"],
            horizontal=True,
            label_visibility="collapsed",
        )

    FILTER_MAP = {
        "All":         None,
        "In progress": "doing",
        "Done":        "done",
        "Not started": "todo",
    }
    filter_status = FILTER_MAP[ch_filter]

    # Card header
    st.markdown(
        f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
        f'border-radius:14px 14px 0 0;padding:12px 18px">'
        f'<div style="font-weight:700;font-size:16px;color:{TEXT}">All chapters</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    any_shown = False
    for ch in chapters:
        num    = ch["num"]
        title  = ch["title"]
        icon   = ch.get("icon", "📄")
        pct    = int(chapter_progress.get(str(num), 0))
        status = ch_status(ch)
        counts = ch_counts.get(num, {"topics": 0, "mcqs": 0, "challenges": 0})

        if filter_status and status != filter_status:
            continue
        if ch_filter == "Not started" and status not in ("todo",):
            continue
        any_shown = True

        locked    = (status == "lock")
        bar_color = SUCCESS if pct >= 100 else ACCENT if pct > 0 else BORDER
        row_opacity = "0.5" if locked else "1"

        c_icon, c_info, c_bar, c_status, c_btn = st.columns([0.5, 2.5, 1.8, 1, 1.2])

        with c_icon:
            st.markdown(
                f'<div style="width:44px;height:44px;border:1.5px solid {BORDER};'
                f'border-radius:10px;display:flex;align-items:center;'
                f'justify-content:center;font-size:22px;'
                f'background:{"#FFF8E0" if status == "doing" else CARD};'
                f'opacity:{row_opacity}">{icon}</div>',
                unsafe_allow_html=True,
            )

        with c_info:
            sub_parts = []
            if counts["topics"]:     sub_parts.append(f"{counts['topics']} topics")
            if counts["mcqs"]:       sub_parts.append(f"{counts['mcqs']} MCQs")
            if counts["challenges"]: sub_parts.append(f"{counts['challenges']} challenges")
            sub_text = " · ".join(sub_parts) if sub_parts else "—"
            st.markdown(
                f'<div style="opacity:{row_opacity};padding:4px 0">'
                f'<div style="font-weight:700;font-size:14px;color:{TEXT}">'
                f'Ch.{num:02d} · {title}</div>'
                f'<div style="font-size:12px;color:{MUTED};margin-top:2px">{sub_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c_bar:
            st.markdown(
                f'<div style="padding:14px 0 0 0;opacity:{row_opacity}">'
                f'<div style="height:8px;border:1.2px solid {BORDER};border-radius:999px;'
                f'background:{CARD};overflow:hidden">'
                f'<div style="width:{pct}%;height:100%;background:{bar_color};'
                f'border-radius:999px"></div></div>'
                f'<div style="font-size:11px;color:{MUTED};margin-top:3px">{pct}% complete</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with c_status:
            status_text  = ("🔒 locked" if locked else
                            ("✓ done" if pct >= 100 else
                             "in progress" if status == "doing" else "not started"))
            status_color = (MUTED if locked else
                            (SUCCESS if pct >= 100 else
                             ACCENT if status == "doing" else MUTED))
            st.markdown(
                f'<div style="padding:10px 0;font-size:13px;font-weight:600;'
                f'color:{status_color}">{status_text}</div>',
                unsafe_allow_html=True,
            )

        with c_btn:
            if locked:
                st.button("🔒 Locked", key=f"ch_btn_{num}", disabled=True, use_container_width=True)
            elif pct >= 100:
                if st.button("Review →", key=f"ch_btn_{num}", use_container_width=True):
                    st.session_state["learn_chapter"] = num
                    st.switch_page("pages/01_learn.py")
            elif status == "doing":
                if st.button("Continue →", key=f"ch_btn_{num}", type="primary", use_container_width=True):
                    st.session_state["learn_chapter"] = num
                    st.switch_page("pages/01_learn.py")
            else:
                if st.button("Start →", key=f"ch_btn_{num}", use_container_width=True):
                    st.session_state["learn_chapter"] = num
                    st.switch_page("pages/01_learn.py")

        # Divider between rows (not after last)
        if ch != chapters[-1]:
            st.markdown(
                f'<div style="border-bottom:1px dashed {BORDER};margin:0"></div>',
                unsafe_allow_html=True,
            )

    if not any_shown:
        st.markdown(
            f'<div style="background:{SURFACE};padding:20px;text-align:center;'
            f'color:{MUTED}">No chapters match this filter.</div>',
            unsafe_allow_html=True,
        )

    # Card footer
    st.markdown(
        f'<div style="background:{SURFACE};border-left:1.5px solid {BORDER};'
        f'border-right:1.5px solid {BORDER};border-bottom:1.5px solid {BORDER};'
        f'border-radius:0 0 14px 14px;height:12px"></div>',
        unsafe_allow_html=True,
    )

    # ── Quick Actions ─────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("📝 Practice MCQ", use_container_width=True):
            st.switch_page("pages/02_mcq.py")
    with qa2:
        if st.button("💻 Coding Challenge", use_container_width=True):
            st.switch_page("pages/03_coding.py")
    with qa3:
        if st.button("📚 Learn a Chapter", use_container_width=True):
            st.switch_page("pages/01_learn.py")
    with qa4:
        if st.button("🤖 Ask AI Tutor", use_container_width=True):
            st.switch_page("pages/04_ai_tutor.py")

except Exception as e:
    log_error("dashboard", e)
    st.error("😅 Something went wrong on this page.")
    st.markdown("**What to do:** Click **💬 Send feedback to Dad** in the sidebar and select '🐛 Something broke'.")
    with st.expander("Technical details (for Dad)"):
        st.code(traceback.format_exc())
