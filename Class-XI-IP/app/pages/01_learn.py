"""
Learn page — Chapter Picker + Two-panel Topic Viewer
CBSE Class XI Informatics Practices (IP Learn)
"""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils import progress as prog_utils
from app.utils.css import inject_theme_css
from app.utils.qr_links import get_link
from app.components.sidebar import render_sidebar

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Learn — IP Learn", page_icon="📖", layout="wide")
st.session_state["_current_page"] = "learn"

CONTENT_DIR = Path(__file__).parent.parent / "content"

CHAPTERS = [
    {"num": 1,  "title": "Introduction to Computer System", "file": "ch01_computer_system.json",      "icon": "🖥️"},
    {"num": 2,  "title": "Programming with Python",          "file": "ch02_programming_python.json",   "icon": "🐍"},
    {"num": 3,  "title": "Python Basics",                    "file": "ch03_python_basics.json",        "icon": "📝"},
    {"num": 4,  "title": "Data Types and Operators",         "file": "ch04_data_types_operators.json", "icon": "🔢"},
    {"num": 5,  "title": "Control Flow Statements",          "file": "ch05_control_flow.json",         "icon": "🔀"},
    {"num": 6,  "title": "List Manipulation",                "file": "ch06_lists.json",                "icon": "📋"},
    {"num": 7,  "title": "Python Dictionary",                "file": "ch07_dictionary.json",           "icon": "📖"},
    {"num": 8,  "title": "Database Concepts",                "file": "ch08_database_concepts.json",    "icon": "🗄️"},
    {"num": 9,  "title": "Structured Query Language",        "file": "ch09_sql.json",                  "icon": "💾"},
    {"num": 10, "title": "Emerging Trends in Technology",    "file": "ch10_emerging_trends.json",      "icon": "🌐"},
]

PYTHON_CHAPTERS = {2, 3, 4, 5, 6, 7}

# ── Session state ─────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = prog_utils.load()
p = st.session_state.progress

render_sidebar(p)
inject_theme_css(p.get("theme", "Dark"))


# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_data
def load_chapter(filename: str) -> dict:
    path = CONTENT_DIR / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def chapter_status(ch_num: int) -> tuple[str, int]:
    """Return (label, pct) for a chapter."""
    visited = ch_num in p.get("chapters_visited", [])
    done_topics = p.get("topics_done", {}).get(str(ch_num), [])
    pct = p.get("chapter_progress", {}).get(str(ch_num), 0)
    if not visited and not done_topics:
        return "Not started", 0
    if pct >= 100:
        return "Done", 100
    return "In progress", pct


def is_locked(ch_num: int) -> bool:
    """Ch 3+ locked until the student has visited Ch 2 (Python intro)."""
    if ch_num <= 2:
        return False
    return 2 not in p.get("chapters_visited", [])


def distribute_concepts(topic_idx: int, total_topics: int, key_concepts: list, topics: list) -> list:
    """
    Evenly distribute key_concepts across topics.
    First try keyword match; if fewer than 2 results, fill from the distributed slice.
    """
    if not key_concepts:
        return []
    # Keyword match first
    stop = {"and", "or", "to", "in", "of", "the", "a", "an", "with", "for",
            "introduction", "getting", "started", "using", "what", "is"}
    topic_name = topics[topic_idx].lower() if topic_idx < len(topics) else ""
    t_words = {w.strip("()&") for w in topic_name.split() if w not in stop}
    matched = [kc for kc in key_concepts
               if t_words & {w.strip("()&") for w in kc["term"].lower().split()}]

    # Deterministic slice — divide concepts evenly across topics
    chunk = max(1, len(key_concepts) // max(total_topics, 1))
    start = (topic_idx * chunk) % len(key_concepts)
    sliced = key_concepts[start: start + chunk + 1]

    # Merge: matched first, then sliced to fill up to ~3 concepts
    seen = {kc["term"] for kc in matched}
    combined = list(matched)
    for kc in sliced:
        if kc["term"] not in seen:
            combined.append(kc)
            seen.add(kc["term"])
    return combined[:4]   # cap at 4 concepts per topic


def find_mcq_for_topic(topic_name: str, mcqs: list) -> dict | None:
    """Find the first MCQ whose topic field matches the current topic."""
    topic_lower = topic_name.lower()
    for q in mcqs:
        q_topic = q.get("topic", "").lower()
        if q_topic in topic_lower or topic_lower in q_topic:
            return q
    return mcqs[0] if mcqs else None


# ── Extra CSS for this page ───────────────────────────────────────────────────
st.markdown("""
<style>
/* pill filter buttons */
div[data-testid="stHorizontalBlock"] .stButton > button {
    border-radius: 999px !important;
    padding: 3px 14px !important;
    font-size: 13px !important;
}
.callout-box {
    background: #FFF8E0;
    border-left: 4px solid #FFC107;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 12px 0;
    color: #1a1a1a;
}
.try-box {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    margin-top: 16px;
}
.ncert-box {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    margin-top: 12px;
}
.diksha-qr {
    width: 52px; height: 52px;
    border: 1.5px solid var(--border);
    background: repeating-conic-gradient(var(--text) 0 25%, transparent 0 50%);
    background-size: 9px 9px;
    border-radius: 4px;
    flex-shrink: 0;
}
/* ── Learn page: topics rail ─────────────────────── */
/* Shrink rail buttons to match content font size */
[data-testid="stVerticalBlock"] .stButton > button {
    font-size: 13px !important;
    padding: 5px 10px !important;
    line-height: 1.45 !important;
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
}

/* Ensure the rail column has a distinct background */
[data-testid="stVerticalBlock"]:first-child {
    background: var(--surface);
    border-right: 1.5px solid var(--border);
    border-radius: 12px 0 0 12px;
    padding: 12px 8px !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 1: CHAPTER PICKER
# ═══════════════════════════════════════════════════════════════════════════════

def render_chapter_picker():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("## Pick a chapter")
    st.caption("10 chapters · roughly 30 min each")

    # ── Filter pills + search ─────────────────────────────────────────────────
    pill_col, _, search_col = st.columns([3, 1, 2])

    with pill_col:
        filter_opt = st.radio(
            "Filter",
            ["All", "In progress", "Not started", "Done"],
            horizontal=True,
            label_visibility="collapsed",
        )

    with search_col:
        search_q = st.text_input("🔍 search topics or keywords…", label_visibility="collapsed",
                                 placeholder="🔍 search topics or keywords…")

    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

    # ── Build visible list ────────────────────────────────────────────────────
    visible = []
    for ch in CHAPTERS:
        status_label, pct = chapter_status(ch["num"])

        if filter_opt == "In progress" and status_label != "In progress":
            continue
        if filter_opt == "Not started" and status_label != "Not started":
            continue
        if filter_opt == "Done" and status_label != "Done":
            continue

        if search_q:
            q_lower = search_q.lower()
            ch_data_preview = load_chapter(ch["file"])
            all_text = ch["title"].lower()
            for kc in ch_data_preview.get("key_concepts", []):
                all_text += " " + kc["term"].lower()
            for t in ch_data_preview.get("topics", []):
                all_text += " " + (t if isinstance(t, str) else t.get("title", t.get("name", ""))).lower()
            if q_lower not in all_text:
                continue

        visible.append((ch, status_label, pct))

    # ── Chapter grid (dashboard-style rows) ──────────────────────────────────
    from app.utils.themes import get_theme
    t = get_theme(p.get("theme", "Dark"))
    SURFACE = t["surface"]; BORDER = t["border"]; ACCENT = t["accent"]
    SUCCESS = t["success"]; MUTED = t["subtext"]; TEXT = t["text"]
    CARD = t["card"]; WARN = t.get("warn", "#FFC107")

    if not visible:
        st.info("No chapters match your filter. Try 'All' to see everything.")
    else:
        # Card container header
        st.markdown(
            f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
            f'border-radius:14px 14px 0 0;padding:12px 18px">'
            f'<div style="font-weight:700;font-size:16px;color:{TEXT}">All chapters</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for i, (ch, status_label, pct) in enumerate(visible):
            locked = is_locked(ch["num"])
            bar_color = SUCCESS if pct >= 100 else ACCENT if pct > 0 else BORDER
            row_opacity = "0.5" if locked else "1"
            status_color = (MUTED if locked else
                            (SUCCESS if pct >= 100 else ACCENT if pct > 0 else MUTED))
            status_text = ("🔒 Locked" if locked else
                           ("✓ Done" if pct >= 100 else
                            "In progress" if pct > 0 else "Not started"))

            # Load topic/mcq/challenge counts from chapter data
            ch_data_preview = load_chapter(ch["file"])
            n_topics     = len(ch_data_preview.get("topics", []))
            n_mcqs       = len(ch_data_preview.get("mcqs", []))
            n_challenges = len(ch_data_preview.get("coding_challenges", []))
            sub_parts = []
            if n_topics:     sub_parts.append(f"{n_topics} topics")
            if n_mcqs:       sub_parts.append(f"{n_mcqs} MCQs")
            if n_challenges: sub_parts.append(f"{n_challenges} challenges")
            sub_text = " · ".join(sub_parts) if sub_parts else "—"

            c_icon, c_info, c_bar, c_status, c_btn = st.columns([0.5, 2.5, 1.8, 1, 1.2])

            with c_icon:
                st.markdown(
                    f'<div style="width:44px;height:44px;border:1.5px solid {BORDER};'
                    f'border-radius:10px;display:flex;align-items:center;'
                    f'justify-content:center;font-size:22px;'
                    f'background:{"#FFF8E0" if pct > 0 and pct < 100 else CARD};'
                    f'opacity:{row_opacity}">{ch["icon"]}</div>',
                    unsafe_allow_html=True,
                )

            with c_info:
                st.markdown(
                    f'<div style="opacity:{row_opacity};padding:4px 0">'
                    f'<div style="font-weight:700;font-size:14px;color:{TEXT}">'
                    f'Ch.{ch["num"]:02d} · {ch["title"]}</div>'
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
                st.markdown(
                    f'<div style="padding:10px 0;font-size:13px;font-weight:600;'
                    f'color:{status_color}">{status_text}</div>',
                    unsafe_allow_html=True,
                )

            with c_btn:
                if locked:
                    st.button("🔒 Locked", key=f"pk_lock_{ch['num']}", disabled=True, use_container_width=True)
                elif pct >= 100:
                    if st.button("Review →", key=f"pk_open_{ch['num']}", use_container_width=True):
                        st.session_state["learn_chapter"] = ch["num"]
                        st.session_state["learn_topic_idx"] = 0
                        st.rerun()
                elif pct > 0:
                    if st.button("Continue →", key=f"pk_open_{ch['num']}", type="primary", use_container_width=True):
                        st.session_state["learn_chapter"] = ch["num"]
                        st.session_state["learn_topic_idx"] = 0
                        st.rerun()
                else:
                    if st.button("Start →", key=f"pk_open_{ch['num']}", use_container_width=True):
                        st.session_state["learn_chapter"] = ch["num"]
                        st.session_state["learn_topic_idx"] = 0
                        st.rerun()

            # Divider between rows (not after the last one)
            if i < len(visible) - 1:
                st.markdown(
                    f'<div style="border-bottom:1px dashed {BORDER};margin:0"></div>',
                    unsafe_allow_html=True,
                )

        # Card footer
        st.markdown(
            f'<div style="background:{SURFACE};border-left:1.5px solid {BORDER};'
            f'border-right:1.5px solid {BORDER};border-bottom:1.5px solid {BORDER};'
            f'border-radius:0 0 14px 14px;height:12px"></div>',
            unsafe_allow_html=True,
        )

    # ── DIKSHA footer ─────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:var(--surface);border:1.5px solid var(--border);
                border-radius:10px;padding:14px 18px;
                display:flex;align-items:center;gap:14px">
        <span style="font-size:26px">📚</span>
        <span style="color:var(--subtext);font-size:14px">
            Each chapter links to CBSE study material on DIKSHA.
            Open any chapter to access the reference link.
        </span>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# VIEW 2: TWO-PANEL CHAPTER VIEWER
# ═══════════════════════════════════════════════════════════════════════════════

def render_chapter_viewer(ch_num: int):
    ch_meta = next((c for c in CHAPTERS if c["num"] == ch_num), None)
    if ch_meta is None:
        st.error("Chapter not found.")
        return

    ch_data = load_chapter(ch_meta["file"])
    if not ch_data:
        st.error(f"Could not load content for Chapter {ch_num}.")
        return

    topics_raw = ch_data.get("topics", [])
    topics: list[str] = [
        t if isinstance(t, str) else t.get("title", t.get("name", f"Topic {i+1}"))
        for i, t in enumerate(topics_raw)
    ]
    total_topics = len(topics)
    key_concepts = ch_data.get("key_concepts", [])
    mcqs = ch_data.get("mcqs", [])
    diksha = get_link(ch_num)

    # ── Theme variables ───────────────────────────────────────────────────────
    from app.utils.themes import get_theme as _get_theme
    _t = _get_theme(p.get("theme", "Dark"))
    SURFACE = _t["surface"]; BORDER = _t["border"]; ACCENT = _t["accent"]
    SUCCESS = _t["success"]; MUTED = _t["subtext"]; TEXT = _t["text"]
    CARD = _t["card"]; WARN = _t.get("warn", "#FFC107")

    # Award +5 XP on first visit
    if ch_num not in p.get("chapters_visited", []):
        updated = prog_utils.visit_chapter(p, ch_num)
        st.session_state.progress = updated

    done_list: list = p.get("topics_done", {}).get(str(ch_num), [])
    topic_idx: int = st.session_state.get("learn_topic_idx", 0)
    topic_idx = max(0, min(topic_idx, total_topics - 1))
    current_topic = topics[topic_idx] if topics else "—"

    # ── Two-panel layout ──────────────────────────────────────────────────────
    rail_col, content_col = st.columns([1, 3])

    # ── LEFT: Topic rail ──────────────────────────────────────────────────────
    with rail_col:
        st.markdown(
            f'<div style="font-family:ui-monospace,monospace;font-size:12px;'
            f'color:var(--subtext);margin-bottom:4px">'
            f'ch.{ch_num:02d} · topics</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-weight:700;font-size:14px;line-height:1.3;margin-bottom:8px">'
            f'{ch_data.get("title", ch_meta["title"])}</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        for i, topic_name in enumerate(topics):
            is_done = i in done_list
            is_current = i == topic_idx
            prefix = "✅ " if is_done else ("▶ " if is_current else "  ")
            if st.button(
                f"{prefix}{topic_name}",
                key=f"rail_{ch_num}_{i}",
                use_container_width=True,
                type="primary" if is_current else "secondary",
            ):
                st.session_state["learn_topic_idx"] = i
                st.rerun()

        st.divider()

        if diksha:
            st.link_button(
                "📚 CBSE Study Material →",
                url=diksha["url"],
                use_container_width=True,
            )

        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        if st.button("← Back to chapters", use_container_width=True):
            del st.session_state["learn_chapter"]
            if "learn_topic_idx" in st.session_state:
                del st.session_state["learn_topic_idx"]
            st.rerun()

    # ── RIGHT: Content area ───────────────────────────────────────────────────
    with content_col:
        # Breadcrumb
        st.caption(f"Learn  ›  Ch.{ch_num:02d}  ›  {current_topic}")

        study_tab, pdf_tab = st.tabs(["📖 Study Guide", "📄 Reference"])

        with study_tab:
            # ── Topic heading ──────────────────────────────────────────────────────
            st.markdown(
                f'<h2 style="margin:0 0 4px 0;font-size:22px;color:{TEXT}">'
                f'{current_topic}</h2>'
                f'<div style="font-size:12px;color:{MUTED};margin-bottom:18px">'
                f'Ch.{ch_num} · Topic {topic_idx + 1} of {total_topics}</div>',
                unsafe_allow_html=True,
            )

            # ── Progress bar ───────────────────────────────────────────────────────
            done_count = len(done_list)
            pct_done   = int(done_count / total_topics * 100) if total_topics else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px">'
                f'<div style="flex:1;height:6px;background:{CARD};border-radius:999px;overflow:hidden">'
                f'<div style="width:{pct_done}%;height:100%;background:{ACCENT};border-radius:999px"></div>'
                f'</div>'
                f'<span style="font-size:12px;color:{MUTED};white-space:nowrap">'
                f'{done_count}/{total_topics} done</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Study guide data lookup ────────────────────────────────────────────
            sg = ch_data.get("study_guide", {})
            topic_lower = current_topic.lower()

            def _sg_lookup(field: str):
                """Look up a study_guide sub-dict by keyword match on topic_lower."""
                sub = sg.get(field, {})
                if not sub:
                    return None
                for kw, val in sub.items():
                    if kw in topic_lower:
                        return val
                return None

            intro_text  = _sg_lookup("intro_by_keyword")
            mnemonic    = _sg_lookup("mnemonics_by_keyword")
            did_u_know  = _sg_lookup("did_you_know_by_keyword")  # list of strings

            # ── "What is it?" card ────────────────────────────────────────────────
            if intro_text:
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,{SURFACE} 0%,{CARD} 100%);'
                    f'border:2px solid {ACCENT};border-radius:14px;'
                    f'padding:18px 22px;margin-bottom:18px">'
                    f'<div style="font-size:11px;color:{MUTED};font-family:ui-monospace,monospace;'
                    f'margin-bottom:8px;letter-spacing:1px">WHAT IS IT?</div>'
                    f'<div style="font-size:15px;color:{TEXT};line-height:1.8">'
                    f'<span style="font-size:22px;margin-right:10px">💡</span>{intro_text}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Key Terms: 2-column grid ───────────────────────────────────────────
            concepts = distribute_concepts(topic_idx, total_topics, key_concepts, topics)
            if concepts:
                st.markdown(
                    f'<div style="font-size:11px;color:{MUTED};font-family:ui-monospace,monospace;'
                    f'margin:0 0 10px 0;letter-spacing:1px">KEY TERMS</div>',
                    unsafe_allow_html=True,
                )
                # Render in pairs for the 2-column grid
                for pair_start in range(0, len(concepts), 2):
                    pair = concepts[pair_start: pair_start + 2]
                    cols = st.columns(len(pair))
                    for col, kc in zip(cols, pair):
                        col.markdown(
                            f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
                            f'border-radius:10px;padding:14px 16px;height:100%">'
                            f'<div style="font-weight:700;font-size:13px;color:{ACCENT};'
                            f'margin-bottom:6px">{kc["term"]}</div>'
                            f'<div style="font-size:13px;color:{TEXT};line-height:1.7">'
                            f'{kc["definition"]}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            elif not intro_text:
                st.info("Key concepts for this topic are being prepared.")

            # ── Real-world analogy ────────────────────────────────────────────────
            _ANALOGIES = {
                "cpu":          "🏏 Think of the CPU like the captain in a cricket match — it directs every player (component) and decides what to do next.",
                "memory":       "📒 RAM is like your rough notepad during an exam — fast to write, but you erase it when you leave. ROM is like a printed textbook — always there, can't easily change it.",
                "storage":      "🗄️ Secondary storage is like your school bag — you carry stuff home and it stays there overnight.",
                "binary":       "🚦 Binary is like a traffic light with only two states: red (0) and green (1). Every number on a computer is built from these two states.",
                "algorithm":    "🍛 An algorithm is like a recipe — a clear list of steps. If you skip a step or do them out of order, the dish goes wrong.",
                "list":         "🛒 A Python list is like a shopping list — ordered, you can add or remove items, and you can look up any item by its position.",
                "dictionary":   "📖 A Python dict is like a real dictionary — you look up a word (key) and instantly get its meaning (value).",
                "function":     "📦 A function is like a reusable machine — give it input, it does work, gives you output. Build it once, use it many times.",
                "loop":         "🔄 A loop is like doing homework problems 1 to 20 — same action, different number each time.",
                "ai":           "🤖 AI is like teaching a child — you show it thousands of examples until it learns the pattern on its own.",
                "cloud":        "☁️ Cloud computing is like renting a flat instead of building your own house — you pay for what you use, no maintenance needed.",
                "cyber":        "🔐 Cybersecurity is like locking your house — you can't stop all criminals, but strong locks make you a much harder target.",
                "blockchain":   "⛓️ Blockchain is like a class register that every student has a copy of — no one can secretly erase an entry.",
                "internet":     "🌐 The Internet is like the road network connecting every city — data travels like vehicles through these roads.",
                "iot":          "💡 IoT is like giving everyday objects (bulbs, fridges, watches) a SIM card so they can talk to each other.",
            }
            analogy_text = None
            for kw, a in _ANALOGIES.items():
                if kw in topic_lower:
                    analogy_text = a
                    break

            if analogy_text:
                st.markdown(
                    f'<div style="background:#FFF8E0;border-left:4px solid #FFC107;'
                    f'border-radius:0 10px 10px 0;padding:14px 18px;margin:14px 0">'
                    f'<div style="font-weight:700;font-size:13px;margin-bottom:6px;color:#5a4000">'
                    f'🌍 Real-world analogy</div>'
                    f'<div style="font-size:14px;color:#333;line-height:1.7">{analogy_text}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Memory trick ──────────────────────────────────────────────────────
            if mnemonic:
                import re as _re
                mnemonic_html = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(mnemonic))
                st.markdown(
                    f'<div style="background:#E8F5E9;border-left:4px solid #4CAF50;'
                    f'border-radius:0 10px 10px 0;padding:14px 18px;margin:14px 0">'
                    f'<div style="font-weight:700;font-size:13px;margin-bottom:6px;color:#1b5e20">'
                    f'🧠 Memory trick</div>'
                    f'<div style="font-size:14px;color:#1b3a1b;line-height:1.7">{mnemonic_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Did you know ──────────────────────────────────────────────────────
            if did_u_know:
                facts = did_u_know if isinstance(did_u_know, list) else [did_u_know]
                for fact in facts[:2]:  # show max 2 facts
                    st.markdown(
                        f'<div style="background:#E3F2FD;border-left:4px solid #2196F3;'
                        f'border-radius:0 10px 10px 0;padding:12px 18px;margin:10px 0">'
                        f'<div style="font-weight:700;font-size:13px;margin-bottom:4px;color:#0d3b6e">'
                        f'🔍 Did you know?</div>'
                        f'<div style="font-size:13px;color:#1a3a5c;line-height:1.7">{fact}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # ── Code example (Python chapters only) ──────────────────────────────
            if ch_num in PYTHON_CHAPTERS and concepts:
                code_lines = []
                for kc in concepts:
                    for fragment in kc["definition"].split("."):
                        fragment = fragment.strip()
                        if any(tok in fragment for tok in
                               ["=", "print(", "range(", "def ", "for ", "if ", "while ",
                                ">>>", "input(", "len(", "append(", "dict(", "list("]):
                            code_lines.append(fragment)
                            if len(code_lines) >= 4:
                                break
                    if len(code_lines) >= 4:
                        break
                if code_lines:
                    st.markdown(
                        f'<div style="font-size:11px;color:{MUTED};'
                        f'font-family:ui-monospace,monospace;margin:18px 0 6px 0;letter-spacing:1px">'
                        f'CODE EXAMPLE</div>',
                        unsafe_allow_html=True,
                    )
                    example = "\n".join(
                        line.split(":")[-1].strip() if ":" in line else line
                        for line in code_lines[:4]
                    )
                    st.code(example, language="python")
                    st.caption("Try running this in the Coding page →")

            # ── Common mistakes ───────────────────────────────────────────────────
            _MISTAKES = {
                "binary":       "⚠️ **Common mistake:** Confusing decimal and binary. Remember: binary uses only 0 and 1. 10 in binary = 2 in decimal, NOT ten!",
                "loop":         "⚠️ **Common mistake:** Off-by-one errors — `range(5)` gives 0,1,2,3,4 (not 0 to 5). Count carefully!",
                "list":         "⚠️ **Common mistake:** Index starts at 0! `my_list[0]` is the first item, not `my_list[1]`.",
                "dictionary":   "⚠️ **Common mistake:** Keys must be unique. If you assign a new value to an existing key, the old value is replaced.",
                "function":     "⚠️ **Common mistake:** Forgetting `return`. A function without `return` gives back `None` — always check if you need to return a value.",
                "ram":          "⚠️ **Common mistake:** Confusing RAM (temporary) with storage (permanent). When power goes off, RAM is wiped — save your work!",
                "cpu":          "⚠️ **Common mistake:** CPU speed alone doesn't determine performance — RAM, storage speed, and the OS all matter too.",
                "algorithm":    "⚠️ **Common mistake:** An algorithm must be finite (must stop eventually) and unambiguous (every step must be crystal clear).",
                "cyber":        "⚠️ **Common mistake:** Thinking a strong password is enough. Combine it with 2FA (two-factor authentication) for real security.",
                "encoding":     "⚠️ **Common mistake:** ASCII can only represent 128 characters (English + symbols). For Hindi or emoji, you need Unicode (UTF-8).",
            }
            mistake_text = None
            for kw, mt in _MISTAKES.items():
                if kw in topic_lower:
                    mistake_text = mt
                    break
            if mistake_text:
                import re as _re2
                mistake_html = _re2.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", mistake_text)
                mistake_html = _re2.sub(r"`(.+?)`", r"<code>\1</code>", mistake_html)
                st.markdown(
                    f'<div style="background:#FFEBEE;border-left:4px solid #E74C3C;'
                    f'border-radius:0 10px 10px 0;padding:12px 18px;margin:14px 0">'
                    f'<div style="font-size:14px;color:#5a0000;line-height:1.7">{mistake_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── Quick check MCQ ───────────────────────────────────────────────────
            q = find_mcq_for_topic(current_topic, mcqs)
            if q:
                ti_key     = f"ti_ans_{ch_num}_{topic_idx}"
                ti_sub_key = f"ti_sub_{ch_num}_{topic_idx}"
                st.markdown(
                    f'<div style="background:{SURFACE};border:2px solid {ACCENT};'
                    f'border-radius:12px;padding:16px 18px;margin:10px 0 4px 0">'
                    f'<div style="font-weight:700;font-size:15px;margin-bottom:2px;color:{TEXT}">'
                    f'🎯 Quick check</div>'
                    f'<div style="font-size:12px;color:{MUTED}">Test your understanding before moving on</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{q['question']}**")
                options     = q.get("options", [])
                correct_idx = q.get("correct_index", 0)
                if not st.session_state.get(ti_sub_key, False):
                    chosen = st.radio("Choose your answer:", options, key=ti_key,
                                      label_visibility="collapsed", index=None)
                    hint_col, check_col, _ = st.columns([1, 1, 3])
                    with hint_col:
                        if st.button("💡 Hint", key=f"hint_{ch_num}_{topic_idx}"):
                            st.info(f"💡 {q.get('explanation', 'Think carefully about the definition.')}")
                    with check_col:
                        if st.button("Check ✓", key=f"check_{ch_num}_{topic_idx}", type="primary"):
                            if chosen is None:
                                st.warning("Pick an answer first!")
                            else:
                                st.session_state[ti_sub_key] = True
                                st.session_state[f"ti_correct_{ch_num}_{topic_idx}"] = (
                                    options.index(chosen) == correct_idx
                                )
                                st.rerun()
                else:
                    was_correct = st.session_state.get(f"ti_correct_{ch_num}_{topic_idx}", False)
                    if was_correct:
                        st.success(f"✅ Correct! +5 XP  {q.get('explanation', '')}")
                    else:
                        st.error(
                            f"Not quite. The answer is **{options[correct_idx]}**.\n\n"
                            f"{q.get('explanation', '')}"
                        )
                    if st.button("Try again", key=f"retry_{ch_num}_{topic_idx}"):
                        del st.session_state[ti_sub_key]
                        st.rerun()

            # ── CBSE Study Material link ──────────────────────────────────────────
            if diksha:
                st.markdown(
                    f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
                    f'border-radius:10px;padding:14px 16px;margin-top:16px">'
                    f'<div style="font-weight:700;margin-bottom:6px;color:{TEXT}">📚 CBSE Study Material</div>'
                    f'<div style="font-size:13px;color:{MUTED}">'
                    f'Official CBSE study material for this chapter →<br>'
                    f'<a href="{diksha["url"]}" target="_blank" style="color:{ACCENT}">'
                    f'Open on DIKSHA ↗</a></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Navigation footer ─────────────────────────────────────────────────
            st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
            prev_col, _, next_col = st.columns([1, 2, 1.4])
            with prev_col:
                if st.button("← Previous", disabled=(topic_idx == 0), use_container_width=True):
                    st.session_state["learn_topic_idx"] = topic_idx - 1
                    st.rerun()
            with next_col:
                already_done = topic_idx in done_list
                btn_label    = "✓ Done · Next →" if already_done else "Mark done · Next →"
                if st.button(btn_label, type="primary", use_container_width=True):
                    updated = prog_utils.mark_topic_done(p, ch_num, topic_idx, total_topics)
                    st.session_state.progress = updated
                    if topic_idx < total_topics - 1:
                        st.session_state["learn_topic_idx"] = topic_idx + 1
                    st.rerun()

            # ── Practice links ────────────────────────────────────────────────────
            st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)
            st.divider()
            st.markdown(
                f'<div style="font-size:13px;color:{MUTED};margin-bottom:8px">'
                f'Practice what you learned in Ch.{ch_num}</div>',
                unsafe_allow_html=True,
            )
            mcq_col, code_col, ai_col = st.columns([1.4, 1.4, 1.6])
            with mcq_col:
                if st.button(f"📝 MCQs for Ch.{ch_num}", use_container_width=True):
                    st.session_state["mcq_chapter_filter"] = ch_num
                    st.switch_page("pages/02_mcq.py")
            with code_col:
                if st.button("💻 Coding challenges", use_container_width=True):
                    st.session_state["coding_chapter_filter"] = ch_num
                    st.switch_page("pages/03_coding.py")
            with ai_col:
                if st.button("🤖 Explain with AI", use_container_width=True):
                    topic_title   = current_topic.get("title", "this topic") if isinstance(current_topic, dict) else str(current_topic)
                    topic_content = current_topic.get("content", "") if isinstance(current_topic, dict) else ""
                    if topic_content:
                        prefill = (
                            f"I'm studying '{topic_title}' in Chapter {ch_num} of my KIPS Class XI IP textbook.\n\n"
                            f"Here's what the book says:\n{topic_content}\n\n"
                            f"Can you explain this more clearly with a simple example?"
                        )
                    else:
                        prefill = f"Can you explain '{topic_title}' from Chapter {ch_num} of Class XI Informatics Practices?"
                    st.session_state["gemini_question"]   = prefill   # launcher mode
                    st.session_state["ai_tutor_prefill"]  = prefill   # integrated mode
                    st.session_state["gemini_chapter_idx"] = ch_num - 1   # 0-based
                    st.switch_page("pages/04_ai_tutor.py")

        with pdf_tab:
            # ── KIPS Reference tab ────────────────────────────────────────────────
            st.markdown(
                f'<div style="background:{SURFACE};border:1.5px solid {BORDER};'
                f'border-radius:12px;padding:16px 20px;margin-bottom:16px">'
                f'<div style="font-size:12px;color:{MUTED};'
                f'font-family:ui-monospace,monospace;margin-bottom:4px">KIPS CHAPTER SUMMARY</div>'
                f'<div style="font-weight:700;font-size:18px;color:{TEXT}">'
                f'Chapter {ch_num}: {ch_data.get("title", "")}</div>'
                f'<div style="font-size:13px;color:{MUTED};margin-top:4px">'
                f'KIPS Informatics Practices Class XI (Code 065)</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            summary = ch_data.get("summary", "")
            if summary:
                st.markdown(
                    f'<div style="background:{CARD};border-left:4px solid {ACCENT};'
                    f'border-radius:0 10px 10px 0;padding:14px 18px;margin-bottom:16px;'
                    f'font-size:14px;color:{TEXT};line-height:1.8">'
                    f'<strong>Chapter Overview</strong><br><br>{summary}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f'<div style="font-weight:700;font-size:15px;color:{TEXT};'
                f'margin:14px 0 10px 0">Topics Covered</div>',
                unsafe_allow_html=True,
            )
            for i, t_raw in enumerate(ch_data.get("topics", []), start=1):
                t_name = t_raw if isinstance(t_raw, str) else t_raw.get("title", t_raw.get("name", f"Topic {i}"))
                t_content = "" if isinstance(t_raw, str) else t_raw.get("content", "")
                st.markdown(
                    f'<div style="padding:10px 0;border-bottom:1px dashed {BORDER}">'
                    f'<div style="display:flex;align-items:flex-start;gap:10px">'
                    f'<span style="font-family:ui-monospace,monospace;font-size:12px;'
                    f'color:{MUTED};min-width:24px;padding-top:2px">{i:02d}.</span>'
                    f'<div><div style="font-size:14px;font-weight:600;color:{TEXT}">{t_name}</div>'
                    + (f'<div style="font-size:13px;color:{MUTED};margin-top:4px;line-height:1.7">{t_content}</div>' if t_content else '')
                    + f'</div></div></div>',
                    unsafe_allow_html=True,
                )

            all_concepts = ch_data.get("key_concepts", [])
            if all_concepts:
                st.markdown(
                    f'<div style="font-weight:700;font-size:15px;color:{TEXT};'
                    f'margin:20px 0 10px 0">Key Concepts & Definitions</div>',
                    unsafe_allow_html=True,
                )
                for kc in all_concepts:
                    st.markdown(
                        f'<div style="border-bottom:1px solid {BORDER};'
                        f'padding:12px 0">'
                        f'<div style="font-weight:700;font-size:14px;color:{ACCENT};'
                        f'margin-bottom:4px">{kc["term"]}</div>'
                        f'<div style="font-size:14px;color:{TEXT};line-height:1.7">'
                        f'{kc["definition"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.info("📖 Place your KIPS Informatics Practices PDF in the Textbook/ folder to enable the book reference tab.")
            if diksha:
                st.link_button("Open CBSE study material on DIKSHA →", url=diksha["url"])


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

ch_num = st.session_state.get("learn_chapter")
if ch_num is None:
    render_chapter_picker()
else:
    render_chapter_viewer(ch_num)
