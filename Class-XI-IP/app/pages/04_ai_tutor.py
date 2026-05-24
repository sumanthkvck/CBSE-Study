"""
AI Tutor page — IP Learn
Two modes:
  • Gemini Launcher (default, no key needed): enriches prompt and opens Google Gemini
  • Integrated Chat (if an API key is configured): full in-app chat with sessions panel
"""
import json
import sys
import urllib.parse
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils import progress as prog_utils
from app.utils.css import inject_theme_css
from app.components.sidebar import render_sidebar
import app.ai.provider as ai

st.set_page_config(page_title="AI Tutor — IP Learn", page_icon="💬", layout="wide")
st.session_state["_current_page"] = "ai_tutor"

# ── Bootstrap ──────────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = prog_utils.load()
p = st.session_state.progress

render_sidebar(p)
inject_theme_css(p.get("theme", "Dark"))

# ── Mode detection ─────────────────────────────────────────────────────────────
integrated_mode = ai.has_any_key()


# ══════════════════════════════════════════════════════════════════════════════
# GEMINI LAUNCHER MODE (no key — the new default)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_content_index() -> list[dict]:
    idx_path = Path(__file__).parent.parent / "content" / "index.json"
    with open(idx_path, encoding="utf-8") as f:
        return json.load(f)["chapters"]


CONTEXT_TEMPLATE = """\
I am a Class XI CBSE student studying Informatics Practices (KIPS textbook, Code 065).
I am currently studying Chapter {num}: {title}.

My question: {question}

Please explain in simple English for a 15-year-old beginner.
Use Indian examples where helpful (cricket, school, UPI, Aadhaar, etc.).\
"""

QUICK_PROMPTS = [
    ("🎯", "Quiz me",       "Give me 5 practice questions on {topic} for CBSE Class XI exam."),
    ("📝", "Exam tips",     "What are the most important points to remember about {topic} for CBSE boards?"),
    ("🐛", "Debug help",    "I have a Python error. Please help me debug this code:\n\n[paste code here]"),
    ("🔄", "Real examples", "Give me 3 real-life Indian examples that explain {topic} clearly."),
]

if not integrated_mode:
    st.markdown("## Ask anything about Class XI IP")
    st.caption("Powered by Google Gemini — free for anyone with a Google account.")

    chapters = load_content_index()
    chapter_options = [f"Ch {c['num']}: {c['title']}" for c in chapters]

    # Default: last visited chapter (from progress), or from "Explain with AI" handoff
    default_ch_idx = p.get("last_chapter", 1) - 1            # 0-based index
    default_ch_idx = st.session_state.pop("gemini_chapter_idx", default_ch_idx)
    default_ch_idx = max(0, min(default_ch_idx, len(chapters) - 1))

    selected_label = st.selectbox(
        "📚 Chapter context",
        chapter_options,
        index=default_ch_idx,
        key="gemini_chapter_sel",
    )
    selected_chapter = chapters[chapter_options.index(selected_label)]

    # Pre-fill from the "Explain with AI" handoff if present
    prefill_question = st.session_state.pop("gemini_question", "")

    question = st.text_area(
        "Your question",
        value=prefill_question,
        placeholder="e.g. What is the difference between a for loop and a while loop?",
        height=110,
        key="gemini_q_input",
    )

    # Enriched prompt preview
    enriched_prompt = CONTEXT_TEMPLATE.format(
        num=selected_chapter["num"],
        title=selected_chapter["title"],
        question=question.strip() if question.strip() else "[type your question above]",
    )

    st.markdown("**What Gemini will receive:**")
    st.code(enriched_prompt, language=None)

    # Open in Gemini button
    gemini_url = "https://gemini.google.com/app?q=" + urllib.parse.quote_plus(enriched_prompt)

    st.link_button(
        "Open in Gemini →",
        url=gemini_url,
        type="primary",
        disabled=not bool(question.strip()),
    )
    st.caption("Opens in a new tab. Paste the prompt if Gemini doesn't pre-fill it.")

    # Quick prompt pills
    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    qp_cols = st.columns(4)
    for col, (icon, label, template) in zip(qp_cols, QUICK_PROMPTS):
        if col.button(f"{icon} {label}", use_container_width=True):
            filled = template.format(topic=selected_chapter["title"])
            st.session_state["gemini_q_input"] = filled
            st.rerun()

    # Upgrade callout
    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
    st.info(
        "💡 **Want AI chat directly inside the app?** "
        "Add a free Gemini API key in Settings — no credit card needed.",
    )

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATED CHAT MODE (API key is configured — keep existing behaviour)
# ══════════════════════════════════════════════════════════════════════════════

GREETING = (
    "Hello! 👋 I'm your Informatics Practices tutor.\n\n"
    "I can help with Python, databases, SQL, and anything from your "
    "Class XI CBSE IP textbook.\n\n"
    "What would you like to learn today?"
)

PROVIDER_LABELS = {
    "gemini":    "⚡ Gemini 2.5 Flash",
    "anthropic": "⚡ Claude Haiku",
    "openai":    "⚡ GPT-4o Mini",
    "offline":   "○ Offline",
}

CHAT_QUICK_PROMPTS = [
    ("📎", "Attach current topic",  "Explain the topic I'm currently studying in simple terms."),
    ("🐍", "Explain my code",       "Can you explain how Python code works step by step?"),
    ("🎯", "Quiz me",               "Give me 3 practice questions on the last topic we discussed."),
    ("📝", "Summarize chapter",     "Give me a short summary of all chapters I should know for my exam."),
]

# ── Session state defaults ─────────────────────────────────────────────────────
if "chat_sessions" not in st.session_state:
    st.session_state["chat_sessions"] = [[{"role": "assistant", "content": GREETING}]]
if "active_session" not in st.session_state:
    st.session_state["active_session"] = 0
if "msg_feedback" not in st.session_state:
    st.session_state["msg_feedback"] = {}  # (session_idx, msg_idx) -> "up" | "down"

# ── Extra CSS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Session list items */
.session-item {
    padding: 8px 10px;
    border-radius: 8px;
    border: 1.5px solid transparent;
    cursor: pointer;
    font-size: 13px;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--subtext);
}
.session-item.active {
    background: var(--surface);
    border-color: var(--accent);
    color: var(--text);
    font-weight: 600;
}
/* Provider / status pills */
.provider-pill {
    display: inline-block;
    border: 1.5px solid var(--border);
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
    background: var(--surface);
}
.status-pill-on {
    display: inline-block;
    border: 1.5px solid #2ED573;
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    color: #2ED573;
    background: var(--surface);
}
.status-pill-off {
    display: inline-block;
    border: 1.5px solid var(--border);
    border-radius: 999px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    color: var(--subtext);
    background: var(--surface);
}
/* Quick-prompt pills (buttons styled as pills) */
div[data-testid="column"] .stButton > button {
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
    border-color: var(--border);
}
/* Feedback buttons (small) */
.stButton > button[kind="secondary"] {
    font-size: 12px;
}
/* Chat input area */
.stChatInput {
    border-top: 1.5px solid var(--border);
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _session_title(messages: list) -> str:
    """Return the first user message (≤30 chars) as the session title."""
    for m in messages:
        if m["role"] == "user":
            txt = m["content"]
            return txt[:28] + "…" if len(txt) > 30 else txt
    return "New chat"


def _build_prompt(messages: list, new_message: str) -> str:
    """
    Pack recent conversation history into a single prompt string.
    Caps at last 10 messages to stay within token limits.
    """
    recent = messages[-10:] if len(messages) > 10 else messages
    lines = []
    if recent:
        lines.append("Previous conversation:")
        for m in recent:
            role_label = "User" if m["role"] == "user" else "Assistant"
            lines.append(f"{role_label}: {m['content']}")
        lines.append("")
    lines.append(f"User: {new_message}")
    return "\n".join(lines)


def _new_chat():
    """Create a fresh session; skip if the current session has no user messages."""
    sessions = st.session_state["chat_sessions"]
    active = st.session_state["active_session"]
    current = sessions[active]
    if len(current) <= 1:
        return
    sessions.append([{"role": "assistant", "content": GREETING}])
    st.session_state["active_session"] = len(sessions) - 1


def _clear_chat():
    """Reset the active session to just the greeting."""
    active = st.session_state["active_session"]
    st.session_state["chat_sessions"][active] = [
        {"role": "assistant", "content": GREETING}
    ]
    st.session_state["msg_feedback"] = {
        k: v for k, v in st.session_state["msg_feedback"].items()
        if k[0] != active
    }


# ── Determine AI state ─────────────────────────────────────────────────────────
provider_name = ai.active_provider()
is_offline = (provider_name == "offline")

# ── Pending / prefill messages (from other pages or quick-prompt buttons) ──────
prefill   = st.session_state.pop("ai_tutor_prefill", None)
pending   = st.session_state.pop("pending_message",  None)
queued    = prefill or pending   # resolved below after chat_input

# Clean up launcher-mode keys so they don't persist across page visits
st.session_state.pop("gemini_question",    None)
st.session_state.pop("gemini_chapter_idx", None)

# ── Page header ────────────────────────────────────────────────────────────────
hdr_left, hdr_right = st.columns([3, 1])
with hdr_left:
    st.markdown("## Ask anything about Class XI IP")
with hdr_right:
    provider_label = PROVIDER_LABELS.get(provider_name, "⚡ " + provider_name.title())
    if is_offline:
        status_html = '<span class="status-pill-off">○ offline</span>'
    else:
        status_html = '<span class="status-pill-on">● connected</span>'
    st.markdown(
        f'<div style="text-align:right;margin-top:10px">'
        f'<span class="provider-pill">{provider_label}</span>&nbsp;'
        f'{status_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Offline warning ────────────────────────────────────────────────────────────
if is_offline:
    st.warning(
        "AI Tutor is offline. Add a free Google Gemini API key in **Settings** to enable it.",
        icon="🔌",
    )

# ── Two-column layout ──────────────────────────────────────────────────────────
col_left, col_right = st.columns([0.9, 3.5])

# ════════════════════════════════════════════════════════════════════════════════
# LEFT: Sessions panel
# ════════════════════════════════════════════════════════════════════════════════
with col_left:
    if st.button("＋ New chat", type="primary", use_container_width=True):
        _new_chat()
        st.rerun()

    st.markdown(
        '<p style="font-size:11px;color:var(--subtext);margin:10px 0 4px">RECENT</p>',
        unsafe_allow_html=True,
    )

    sessions = st.session_state["chat_sessions"]
    active   = st.session_state["active_session"]

    for i, sess in enumerate(sessions):
        title  = _session_title(sess)
        is_act = (i == active)
        if st.button(
            title,
            key=f"sess_{i}",
            use_container_width=True,
            type="primary" if is_act else "secondary",
        ):
            if not is_act:
                st.session_state["active_session"] = i
                st.rerun()

    # Footer
    st.markdown("<br>", unsafe_allow_html=True)
    if not is_offline:
        st.markdown(
            '<p style="font-size:11px;color:var(--subtext)">🪙 unlimited<br>(Gemini free tier)</p>',
            unsafe_allow_html=True,
        )

# ════════════════════════════════════════════════════════════════════════════════
# RIGHT: Chat area
# ════════════════════════════════════════════════════════════════════════════════
with col_right:
    active   = st.session_state["active_session"]
    sessions = st.session_state["chat_sessions"]
    messages = sessions[active]

    # ── Chat history ───────────────────────────────────────────────────────────
    last_assistant_idx = None
    for idx, msg in enumerate(messages):
        if msg["role"] == "assistant":
            last_assistant_idx = idx

    for idx, msg in enumerate(messages):
        role   = msg["role"]
        avatar = "🧑" if role == "user" else "🤖"

        with st.chat_message(role, avatar=avatar):
            st.markdown(msg["content"])

            # Follow-up action buttons — only after the LAST assistant message
            if role == "assistant" and idx == last_assistant_idx and idx > 0:
                fb_key = (active, idx)
                given  = st.session_state["msg_feedback"].get(fb_key)

                act1, act2, act3, act4 = st.columns([2, 2, 1, 1])
                with act1:
                    if st.button("🎯 Quiz me", key=f"quiz_{active}_{idx}"):
                        st.session_state["pending_message"] = (
                            "Give me 3 practice questions on this topic."
                        )
                        st.rerun()
                with act2:
                    if st.button("🔄 Explain differently", key=f"rephrase_{active}_{idx}"):
                        st.session_state["pending_message"] = (
                            "Explain that in simpler terms."
                        )
                        st.rerun()
                with act3:
                    up_type = "primary" if given == "up" else "secondary"
                    if st.button("👍", key=f"up_{active}_{idx}", type=up_type):
                        st.session_state["msg_feedback"][fb_key] = "up"
                        st.rerun()
                with act4:
                    dn_type = "primary" if given == "down" else "secondary"
                    if st.button("👎", key=f"dn_{active}_{idx}", type=dn_type):
                        st.session_state["msg_feedback"][fb_key] = "down"
                        st.rerun()

    # ── Clear chat ─────────────────────────────────────────────────────────────
    if len(messages) > 1:
        if st.button("🗑 Clear chat", type="secondary"):
            _clear_chat()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick-prompt pills ─────────────────────────────────────────────────────
    qp_cols = st.columns(len(CHAT_QUICK_PROMPTS))
    for col, (icon, label, prompt_text) in zip(qp_cols, CHAT_QUICK_PROMPTS):
        with col:
            if st.button(f"{icon} {label}", key=f"qp_{label}", disabled=is_offline):
                st.session_state["pending_message"] = prompt_text
                st.rerun()

    # ── Composer ───────────────────────────────────────────────────────────────
    user_input = st.chat_input(
        "ask anything about your syllabus…",
        disabled=is_offline,
    )

    st.caption("⚠️ AI replies may be wrong — verify with your KIPS textbook.")

    # ── Send logic ─────────────────────────────────────────────────────────────
    message = queued or user_input
    if message and not is_offline:
        # Append user message
        messages.append({"role": "user", "content": message})

        # Build context-aware prompt and get AI response
        prompt = _build_prompt(messages[:-1], message)  # history before this msg
        with st.spinner("Thinking…"):
            reply = ai.ask(prompt)

        messages.append({"role": "assistant", "content": reply})
        st.rerun()
