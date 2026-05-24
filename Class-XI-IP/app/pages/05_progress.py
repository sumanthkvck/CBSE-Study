"""
Progress page — mastery bars, daily activity chart, badges, reset.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils import progress as prog_utils
from app.utils.css import inject_theme_css
from app.utils.themes import get_theme
from app.components.sidebar import render_sidebar

st.set_page_config(
    page_title="My Progress — IP Learn",
    page_icon="📊",
    layout="wide",
)
st.session_state["_current_page"] = "progress"

# ── Load progress ──────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = prog_utils.load()
p = st.session_state.progress

render_sidebar(p)
inject_theme_css(p.get("theme", "Dark"))

# ── Load chapter index ─────────────────────────────────────────────────────────
_INDEX_FILE = Path(__file__).parent.parent / "content" / "index.json"
CHAPTERS = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))["chapters"]

# ── Load solved coding count per chapter ──────────────────────────────────────
def _count_solved(p: dict) -> tuple[int, int]:
    """Return (solved, total) across all challenges."""
    solved = len(p.get("solved_coding", []))
    # count total challenges across all content files
    total = 0
    content_dir = Path(__file__).parent.parent / "content"
    for ch in CHAPTERS:
        try:
            data = json.loads((content_dir / ch["file"]).read_text(encoding="utf-8"))
            total += len(data.get("coding_challenges", []))
        except Exception:
            pass
    return solved, total


# ── Badge definitions & unlock logic ──────────────────────────────────────────
BADGE_DEFS = [
    {
        "id": "first_quiz",
        "icon": "🥇",
        "name": "First quiz",
        "check": lambda p: p.get("mcq_total", 0) >= 1,
    },
    {
        "id": "streak_7",
        "icon": "🔥",
        "name": "7-day streak",
        "check": lambda p: p.get("streak", 0) >= 7,
    },
    {
        "id": "hello_python",
        "icon": "🐍",
        "name": "Hello Python",
        "check": lambda p: any(
            s.startswith("ch05") or "python" in s.lower()
            for s in p.get("solved_coding", [])
        ),
    },
    {
        "id": "perfect_run",
        "icon": "💯",
        "name": "Perfect MCQ run",
        "check": lambda p: p.get("perfect_run_achieved", False),
    },
    {
        "id": "marathoner",
        "icon": "🏃",
        "name": "Marathoner",
        "check": lambda p: p.get("mcq_total", 0) >= 50,
    },
    {
        "id": "level_5",
        "icon": "⭐",
        "name": "Level 5",
        "check": lambda p: p.get("xp", 0) >= 2000,
    },
]


def check_and_award_badges(p: dict) -> dict:
    """Unlock any newly-earned badges and save if changed."""
    earned = list(p.get("badges_earned", []))
    changed = False
    for bd in BADGE_DEFS:
        if bd["id"] not in earned and bd["check"](p):
            earned.append(bd["id"])
            changed = True
    if changed:
        p["badges_earned"] = earned
        prog_utils.save(p)
    return p


# Award badges on page load
p = check_and_award_badges(p)
st.session_state.progress = p

# ── Theme colors (for inline HTML) ────────────────────────────────────────────
t = get_theme(p.get("theme", "Dark"))
ACCENT  = t["accent"]
SUCCESS = t["success"]
BORDER  = t["border"]
SURFACE = t["surface"]
CARD    = t["card"]
MUTED   = t["subtext"]
TEXT    = t["text"]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE TITLE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f'<h1 style="margin-top:4px;margin-bottom:2px">Your progress</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<p style="color:{MUTED};margin-top:0;margin-bottom:20px">Little wins, every day.</p>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# STATS ROW — 4 metric cards
# ══════════════════════════════════════════════════════════════════════════════
xp      = p.get("xp", 0)
streak  = p.get("streak", 0)
mcq_ok  = p.get("mcq_correct", 0)
solved, total_challenges = _count_solved(p)

def _metric_card(label: str, value: str, icon: str) -> str:
    return f"""
    <div style="
        background:{SURFACE};
        border:1.5px solid {BORDER};
        border-radius:12px;
        padding:16px 18px;
    ">
        <div style="font-size:13px;color:{MUTED}">{label}</div>
        <div style="display:flex;align-items:baseline;gap:6px;margin-top:4px">
            <div style="font-size:28px;font-weight:700">{value}</div>
            <div style="font-size:20px">{icon}</div>
        </div>
    </div>"""

c1, c2, c3, c4 = st.columns(4)
c1.markdown(_metric_card("Total XP", f"{xp:,}", "🎉"), unsafe_allow_html=True)
c2.markdown(_metric_card("Streak", f"{streak} days", "🔥"), unsafe_allow_html=True)
c3.markdown(_metric_card("MCQs correct", str(mcq_ok), "✅"), unsafe_allow_html=True)
c4.markdown(_metric_card("Code passed", f"{solved} / {total_challenges}", "🐍"), unsafe_allow_html=True)

st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT — left (chapter mastery) | right (activity + badges)
# ══════════════════════════════════════════════════════════════════════════════
left, right = st.columns([1.6, 1])

# ── LEFT: Chapter mastery ──────────────────────────────────────────────────────
with left:
    # Card header
    st.markdown(f"""
    <div style="background:{SURFACE};border:1.5px solid {BORDER};
                border-radius:14px 14px 0 0;padding:20px 22px 12px 22px">
        <div style="font-weight:700;font-size:16px;color:{TEXT}">Chapter mastery</div>
        <div style="height:3px;width:70px;background:{ACCENT};
                    border-radius:99px;margin:6px 0 0 0"></div>
    </div>
    """, unsafe_allow_html=True)

    # One markdown call per row — avoids large-block rendering issues
    for ch in CHAPTERS:
        num = ch["num"]
        title = ch["title"]
        pct = int(p.get("chapter_progress", {}).get(str(num), 0))
        bar_color = SUCCESS if pct == 100 else ACCENT if pct > 0 else BORDER
        st.markdown(f"""
        <div style="background:{SURFACE};border-left:1.5px solid {BORDER};
                    border-right:1.5px solid {BORDER};border-bottom:1px solid {BORDER};
                    padding:8px 22px">
            <div style="display:grid;grid-template-columns:36px 1.5fr 1.6fr 48px;
                        gap:10px;align-items:center">
                <div style="font-family:ui-monospace,monospace;color:{MUTED};font-size:14px">
                    {str(num).zfill(2)}
                </div>
                <div style="font-weight:600;font-size:14px;white-space:nowrap;
                            overflow:hidden;text-overflow:ellipsis;color:{TEXT}">{title}</div>
                <div style="height:10px;border:1.5px solid {BORDER};border-radius:99px;
                            background:{CARD};overflow:hidden">
                    <div style="width:{pct}%;height:100%;background:{bar_color};
                                border-radius:99px"></div>
                </div>
                <div style="text-align:right;font-family:ui-monospace,monospace;
                            font-size:13px;color:{MUTED}">{pct}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Card footer
    st.markdown(f"""
    <div style="background:{SURFACE};border-left:1.5px solid {BORDER};
                border-right:1.5px solid {BORDER};border-bottom:1.5px solid {BORDER};
                border-radius:0 0 14px 14px;height:12px"></div>
    """, unsafe_allow_html=True)

# ── RIGHT: Activity chart + Badges ────────────────────────────────────────────
with right:

    # ── Daily activity chart ─────────────────────────────────────────────────
    daily_xp = p.get("daily_xp", {})
    today = datetime.now().date()

    # Fallback: if no daily data but student has XP, show today's total
    if not daily_xp and xp > 0:
        daily_xp = {today.strftime("%Y-%m-%d"): xp}

    max_xp = max((daily_xp.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), 0)
                  for i in range(30)), default=1)
    max_xp = max(max_xp, 1)

    bars_html = ""
    for i in range(29, -1, -1):
        day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        v = daily_xp.get(day, 0)
        height_pct = int(v / max_xp * 88) if v > 0 else 4
        bar_color = ACCENT if v >= 30 else "#bdb6e6" if v >= 10 else MUTED
        bars_html += (
            f'<div style="flex:1;height:64px;display:flex;align-items:flex-end">'
            f'<div style="width:100%;height:{height_pct}%;background:{bar_color};'
            f'border:1px solid {BORDER};border-radius:2px;min-height:3px"'
            f' title="{day}: {v} XP"></div></div>'
        )

    st.markdown(
        f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
        f'border-radius:14px;padding:16px 18px 8px 18px;margin-bottom:14px">'
        f'<div style="font-weight:700;font-size:15px;color:{TEXT}">Daily activity (last 30 days)</div>'
        f'<div style="display:flex;gap:3px;height:68px;align-items:flex-end;margin-top:12px">'
        f'{bars_html}</div>'
        f'<div style="display:flex;justify-content:space-between;'
        f'margin-top:4px;font-size:11px;color:{MUTED}">'
        f'<span>30 days ago</span><span>today</span></div></div>',
        unsafe_allow_html=True,
    )

    # ── Badges ───────────────────────────────────────────────────────────────
    earned_ids = p.get("badges_earned", [])

    # Card header
    st.markdown(
        f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
        f'border-radius:14px 14px 0 0;padding:16px 18px 8px 18px">'
        f'<div style="font-weight:700;font-size:15px;color:{TEXT}">Badges</div></div>',
        unsafe_allow_html=True,
    )

    # Badge grid — one markdown per badge to avoid large-block rendering issues
    cols = st.columns(len(BADGE_DEFS))
    for col, bd in zip(cols, BADGE_DEFS):
        unlocked = bd["id"] in earned_ids
        opacity = "1" if unlocked else "0.45"
        icon = bd["icon"] if unlocked else "🔒"
        bg = SURFACE if unlocked else CARD
        with col:
            st.markdown(
                f'<div style="padding:10px 6px;border:1.5px solid {BORDER};'
                f'border-radius:10px;display:flex;flex-direction:column;'
                f'align-items:center;gap:4px;background:{bg};opacity:{opacity}">'
                f'<div style="font-size:22px">{icon}</div>'
                f'<div style="font-size:11px;text-align:center;color:{MUTED};'
                f'line-height:1.3">{bd["name"]}</div></div>',
                unsafe_allow_html=True,
            )

    # Card footer
    st.markdown(
        f'<div style="background:{SURFACE};border-left:1.5px solid {BORDER};'
        f'border-right:1.5px solid {BORDER};border-bottom:1.5px solid {BORDER};'
        f'border-radius:0 0 14px 14px;height:12px"></div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# RESET SECTION
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
st.divider()

st.subheader("⚠️ Reset Progress")
st.caption(
    "This will clear all XP, streak, MCQ history, coding progress, and badges. "
    "Your name, theme, API keys, and onboarding status are preserved."
)

confirmed = st.checkbox("I understand — reset all my progress data")
if confirmed:
    if st.button("🗑 Reset all progress", type="primary"):
        # Preserve identity / settings
        keep = {
            "name":         p.get("name", ""),
            "onboarded":    p.get("onboarded", False),
            "theme":        p.get("theme", "Dark"),
            "code_theme":   p.get("code_theme", "monokai"),
            "daily_xp_goal":p.get("daily_xp_goal", 50),
            "ai_provider":  p.get("ai_provider", "gemini"),
            "goal":         p.get("goal", ""),
        }
        fresh = {**prog_utils.DEFAULT, **keep}
        prog_utils.save(fresh)
        st.session_state.progress = fresh
        st.success("Progress reset. Starting fresh! 🎉")
        st.rerun()
