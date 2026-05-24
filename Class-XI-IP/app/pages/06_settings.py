"""
Settings page — 2×2 grid (Profile, AI Keys, Theme, Data) + first-run onboarding flow.
"""
import json
import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils import progress as prog_utils
from app.utils.css import inject_theme_css
from app.utils.themes import get_theme, THEMES, theme_names
from app.components.sidebar import render_sidebar
from app.utils.feedback import load_feedback
from app.utils.errors import read_recent_errors

st.set_page_config(
    page_title="Settings — IP Learn",
    page_icon="⚙️",
    layout="wide",
)
st.session_state["_current_page"] = "settings"

# ── Key-file helpers ───────────────────────────────────────────────────────────
KEY_FILE = Path.home() / ".iplearn_keys"
_PROVIDERS = ["GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]


def load_saved_keys() -> dict:
    keys = {k: "" for k in _PROVIDERS}
    if KEY_FILE.exists():
        for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k in keys:
                    keys[k] = v
    return keys


def save_keys(keys: dict):
    lines = [f"{k}={v}" for k, v in keys.items() if v]
    KEY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in keys.items():
        if v:
            os.environ[k] = v


def _mask(val: str) -> str:
    if not val:
        return "not set"
    return val[:4] + "•••••••••••" + val[-3:] if len(val) > 8 else "••••"


def _key_status(val: str) -> tuple:
    """Return (status label, css class)."""
    if val:
        return "● connected", "success"
    return "○ optional", "muted"


# ── Load progress ──────────────────────────────────────────────────────────────
if "progress" not in st.session_state:
    st.session_state.progress = prog_utils.load()
p = st.session_state.progress


# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING FLOW
# ══════════════════════════════════════════════════════════════════════════════

def _onboard_topbar(step: int, total: int, t: dict):
    """Render the top bar with IP logo, step dots, and step label."""
    accent  = t["accent"]
    success = t["success"]
    border  = t["border"]
    muted   = t["subtext"]

    dots_html = "".join(
        f'<div style="width:36px;height:8px;border:1.2px solid {border};border-radius:99px;'
        f'background:{success if i < step else accent if i == step else border}"></div>'
        for i in range(1, total + 1)
    )

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;
                padding:14px 4px 14px 4px;border-bottom:1.5px solid {border};
                margin-bottom:28px">
        <div style="width:32px;height:32px;border:1.5px solid {border};
                    background:{accent};border-radius:8px;color:#fff;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:700;font-size:14px;flex-shrink:0">IP</div>
        <div style="font-weight:700">IP Learn — Setup</div>
        <div style="flex:1"></div>
        <div style="display:flex;gap:6px">{dots_html}</div>
        <span style="font-size:13px;color:{muted};
                     font-family:ui-monospace,monospace">step {step} / {total}</span>
    </div>
    """, unsafe_allow_html=True)


def render_onboarding(p: dict):
    """Full-screen onboarding — replaces settings page on first run."""
    inject_theme_css(p.get("theme", "Dark"))
    t = get_theme(p.get("theme", "Dark"))
    accent  = t["accent"]
    border  = t["border"]
    surface = t["surface"]
    card    = t["card"]
    muted   = t["subtext"]
    text    = t["text"]
    success = t["success"]

    if "onboard_step" not in st.session_state:
        st.session_state.onboard_step = 1
    step = st.session_state.onboard_step

    _onboard_topbar(step, 4, t)

    # ── Step 1: Welcome ───────────────────────────────────────────────────────
    if step == 1:
        st.markdown(f"""
        <div style="text-align:center;margin-top:20px;margin-bottom:28px">
            <div style="font-size:52px">👋</div>
            <div style="font-size:34px;font-weight:700;margin-top:10px">Welcome to IP Learn!</div>
            <div style="height:3px;width:140px;background:{accent};
                        border-radius:99px;margin:10px auto 0 auto"></div>
            <div style="color:{muted};font-size:16px;margin-top:14px;line-height:1.6">
                An interactive way to learn Class XI Informatics Practices (CBSE 065).<br>
                Built for you — no programming background needed.
            </div>
        </div>
        """, unsafe_allow_html=True)

        f1, f2, f3 = st.columns(3)
        for col, icon, title, desc in [
            (f1, "📖", "10 chapters",    "KIPS-aligned, original explanations"),
            (f2, "🐍", "Hands-on Python", "Code right in your browser"),
            (f3, "💬", "AI tutor",        "Stuck? Ask anything, anytime"),
        ]:
            col.markdown(f"""
            <div style="background:{surface};border:1.5px solid {border};
                        border-radius:12px;padding:16px;height:100px">
                <div style="font-size:26px">{icon}</div>
                <div style="font-weight:700;margin-top:6px">{title}</div>
                <div style="color:{muted};font-size:13px;margin-top:4px">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        bl, br = st.columns(2)
        with bl:
            if st.button("Skip setup", use_container_width=True):
                p["onboarded"] = True
                prog_utils.save(p)
                st.session_state.progress = p
                st.rerun()
        with br:
            if st.button("Let's go →", type="primary", use_container_width=True):
                st.session_state.onboard_step = 2
                st.rerun()

    # ── Step 2: Profile ───────────────────────────────────────────────────────
    elif step == 2:
        st.markdown(f"""
        <div style="margin-bottom:18px">
            <div style="font-size:28px;font-weight:700">Tell us about yourself</div>
            <div style="height:3px;width:80px;background:{accent};
                        border-radius:99px;margin:8px 0 6px 0"></div>
            <div style="color:{muted}">So we can greet you and track your progress.</div>
        </div>
        """, unsafe_allow_html=True)

        # Constrain width
        _, centre, _ = st.columns([1, 3, 1])
        with centre:
            name = st.text_input("Your name", value=p.get("name", ""), placeholder="e.g. Aarav")

            st.markdown(
                f'<div style="font-size:13px;color:{muted};margin-top:8px;margin-bottom:6px">'
                f"What's your goal?</div>",
                unsafe_allow_html=True,
            )

            goals = [
                ("🎯 Score 90+ in board exams", "score_90"),
                ("🐍 Learn Python from scratch", "learn_python"),
                ("📚 Daily revision practice",  "daily_revision"),
                ("🤔 Just exploring",            "just_exploring"),
            ]
            current_goal = st.session_state.get("ob2_goal", p.get("goal", goals[0][1]))
            ga, gb = st.columns(2)
            goal_cols_map = [ga, gb, ga, gb]
            for i, (label, gid) in enumerate(goals):
                selected = gid == current_goal
                bg = "#FFF8E0" if selected else surface
                bc = accent if selected else border
                if goal_cols_map[i].button(
                    ("✅ " if selected else "") + label,
                    key=f"goal_{gid}",
                    use_container_width=True,
                ):
                    st.session_state.ob2_goal = gid
                    st.rerun()

            st.markdown(
                f'<div style="font-size:13px;color:{muted};margin-top:16px;margin-bottom:6px">'
                f"Daily XP goal</div>",
                unsafe_allow_html=True,
            )
            current_xp_goal = st.session_state.get("ob2_xp", p.get("daily_xp_goal", 50))
            xp_cols = st.columns(4)
            for i, gv in enumerate([30, 50, 100, 200]):
                sel = gv == current_xp_goal
                if xp_cols[i].button(
                    f"{'✓ ' if sel else ''}{gv} XP",
                    key=f"xpgoal_{gv}",
                    use_container_width=True,
                    type="primary" if sel else "secondary",
                ):
                    st.session_state.ob2_xp = gv
                    st.rerun()

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            bl2, br2 = st.columns(2)
            with bl2:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboard_step = 1
                    st.rerun()
            with br2:
                if st.button("Continue →", type="primary", use_container_width=True):
                    if name.strip():
                        p["name"] = name.strip()
                    p["goal"] = st.session_state.get("ob2_goal", current_goal)
                    p["daily_xp_goal"] = st.session_state.get("ob2_xp", current_xp_goal)
                    prog_utils.save(p)
                    st.session_state.progress = p
                    st.session_state.onboard_step = 3
                    st.rerun()

    # ── Step 3: API Key ───────────────────────────────────────────────────────
    elif step == 3:
        st.markdown(f"""
        <div style="margin-bottom:18px">
            <div style="font-size:28px;font-weight:700">Add an AI key (optional)</div>
            <div style="height:3px;width:90px;background:{accent};
                        border-radius:99px;margin:8px 0 6px 0"></div>
            <div style="color:{muted}">Unlocks the AI Tutor. All other features work without it.</div>
        </div>
        """, unsafe_allow_html=True)

        _, centre, _ = st.columns([1, 3, 1])
        with centre:
            st.markdown(f"""
            <div style="background:{card};border:1.5px solid {border};
                        border-radius:12px;padding:16px;margin-bottom:16px">
                <div style="font-weight:700;margin-bottom:8px">🎁 Free Google Gemini key (recommended)</div>
                <ol style="margin:0 0 0 18px;color:{muted};line-height:1.9;font-size:14px">
                    <li>Visit <code>aistudio.google.com/apikey</code></li>
                    <li>Sign in with your Google account · no credit card needed</li>
                    <li>Click "Create API key" → copy → paste below</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

            api_key = st.text_input(
                "Paste your key",
                type="password",
                placeholder="AIza...",
                key="onboard_api_key",
            )
            st.caption("Stored locally in `~/.iplearn_keys` — never sent anywhere except the AI provider.")
            st.caption("Also supports Anthropic Claude and OpenAI.")

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            bl3, mid3, br3 = st.columns(3)
            with bl3:
                if st.button("← Back", use_container_width=True):
                    st.session_state.onboard_step = 2
                    st.rerun()
            with mid3:
                if st.button("Skip for now", use_container_width=True):
                    st.session_state.onboard_step = 4
                    st.rerun()
            with br3:
                if st.button("Verify & continue →", type="primary", use_container_width=True):
                    key_val = api_key.strip()
                    if not key_val:
                        st.warning("Paste a key first, or click 'Skip for now'.")
                    else:
                        with st.spinner("Checking key…"):
                            try:
                                import google.generativeai as genai
                                genai.configure(api_key=key_val)
                                m = genai.GenerativeModel("gemini-2.5-flash")
                                m.generate_content("ping")
                                save_keys({"GEMINI_API_KEY": key_val,
                                           "ANTHROPIC_API_KEY": "",
                                           "OPENAI_API_KEY": ""})
                                st.success("Key verified!")
                                st.session_state.onboard_step = 4
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not verify key: {e}")

    # ── Step 4: Done ──────────────────────────────────────────────────────────
    elif step == 4:
        name = p.get("name", "Student") or "Student"

        st.markdown(f"""
        <div style="text-align:center;margin-top:30px;margin-bottom:28px">
            <div style="font-size:56px">🎉</div>
            <div style="font-size:32px;font-weight:700;margin-top:8px">
                You're all set, {name}!
            </div>
            <div style="height:3px;width:130px;background:{accent};
                        border-radius:99px;margin:10px auto 0 auto"></div>
            <div style="color:{muted};margin-top:10px">
                Start with Chapter 1 — Computer System. Earn XP, keep a streak, have fun.
            </div>
        </div>
        """, unsafe_allow_html=True)

        _, centre, _ = st.columns([1, 3, 1])
        with centre:
            st.markdown(f"""
            <div style="background:#FFF8E0;border:1.5px solid #FFB300;
                        border-radius:12px;padding:16px 20px;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:14px">
                    <div style="font-size:28px">📍</div>
                    <div>
                        <div style="font-weight:700;color:#1a1a1a">Suggested first lesson</div>
                        <div style="color:#666;font-size:14px;margin-top:2px">
                            Ch.01 · What is a computer? — 4 topics, ~12 min
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Start lesson →", type="primary", use_container_width=True):
                p["onboarded"] = True
                prog_utils.save(p)
                st.session_state.progress = p
                st.switch_page("pages/01_learn.py")

            lc, rc = st.columns(2)
            with lc:
                if st.button("🏠 Go to home", use_container_width=True):
                    p["onboarded"] = True
                    prog_utils.save(p)
                    st.session_state.progress = p
                    st.switch_page("main.py")
            with rc:
                if st.button("⚙ Change settings", use_container_width=True):
                    p["onboarded"] = True
                    prog_utils.save(p)
                    st.session_state.progress = p
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING GATE
# ══════════════════════════════════════════════════════════════════════════════
if not p.get("onboarded", False):
    render_onboarding(p)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS PAGE (post-onboarding)
# ══════════════════════════════════════════════════════════════════════════════
render_sidebar(p)
inject_theme_css(p.get("theme", "Dark"))

t = get_theme(p.get("theme", "Dark"))
accent  = t["accent"]
border  = t["border"]
surface = t["surface"]
card    = t["card"]
muted   = t["subtext"]
text    = t["text"]
success = t["success"]
danger  = t["danger"]

# Page title
st.markdown('<h1 style="margin-top:4px;margin-bottom:2px">Settings</h1>', unsafe_allow_html=True)
st.markdown(
    f'<p style="color:{muted};margin-top:0;margin-bottom:20px">'
    f'Your data stays on your computer.</p>',
    unsafe_allow_html=True,
)


def _section_header(title: str, underline_w: int = 50):
    """Render a bold title with accent underline bar."""
    st.markdown(f"""
    <div style="font-weight:700;font-size:15px">{title}</div>
    <div style="height:3px;width:{underline_w}px;background:{accent};
                border-radius:99px;margin:6px 0 14px 0"></div>
    """, unsafe_allow_html=True)


# ── Top row: Profile | AI Keys ─────────────────────────────────────────────────
col_left, col_right = st.columns(2)

# ════════════ BOX 1 — Profile ════════════
with col_left:
    with st.container(border=True):
        _section_header("👤 Profile", 50)

        new_name = st.text_input(
            "Your name",
            value=p.get("name", ""),
            placeholder="e.g. Aarav",
            key="settings_name",
        )

        st.markdown(
            f'<div style="font-size:13px;color:{muted}">Class / Board</div>'
            f'<div style="font-family:ui-monospace,monospace;font-size:14px;'
            f'background:{card};border:1.5px solid {border};border-radius:8px;'
            f'padding:8px 10px;margin-bottom:12px">XI · CBSE (065)</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div style="font-size:13px;color:{muted};margin-bottom:6px">Daily XP goal</div>',
            unsafe_allow_html=True,
        )
        current_xp = p.get("daily_xp_goal", 50)
        chosen_xp = current_xp
        xp_btn_cols = st.columns(4)
        for i, gv in enumerate([30, 50, 100, 200]):
            sel = gv == current_xp
            if xp_btn_cols[i].button(
                f"{'✓ ' if sel else ''}{gv} XP",
                key=f"xp_set_{gv}",
                type="primary" if sel else "secondary",
                use_container_width=True,
            ):
                chosen_xp = gv

        if st.button("Save profile", type="primary", key="save_profile"):
            if new_name.strip():
                p["name"] = new_name.strip()
            p["daily_xp_goal"] = chosen_xp
            prog_utils.save(p)
            st.session_state.progress = p
            st.success("Profile saved!")
            st.rerun()

# ════════════ BOX 2 — AI Provider Keys ════════════
with col_right:
    with st.container(border=True):
        _section_header("🔑 AI provider keys (optional)", 70)
        st.markdown(
            "The AI Tutor works without a key — it opens Google Gemini in your browser. "
            "Add a key below only if you want in-app chat."
        )
        st.link_button("Get a free Gemini API key →", url="https://aistudio.google.com/apikey")

        saved_keys = load_saved_keys()
        key_inputs = {}

        for prov in _PROVIDERS:
            current_val = saved_keys.get(prov, "") or os.environ.get(prov, "")
            status_label, status_cls = _key_status(current_val)
            status_color = success if status_cls == "success" else muted

            kcol1, kcol2, kcol3 = st.columns([1.4, 1.6, 0.9])
            kcol1.markdown(
                f'<div style="font-family:ui-monospace,monospace;font-size:12px;'
                f'padding-top:10px;color:{muted}">{prov}</div>',
                unsafe_allow_html=True,
            )
            key_inputs[prov] = kcol2.text_input(
                prov,
                value=current_val,
                type="password",
                label_visibility="collapsed",
                placeholder="not set",
                key=f"key_{prov}",
            )
            kcol3.markdown(
                f'<div style="font-size:13px;color:{status_color};padding-top:10px">'
                f'{status_label}</div>',
                unsafe_allow_html=True,
            )

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            with st.expander("How do I get a free key?"):
                st.markdown(
                    "1. Go to **aistudio.google.com/apikey**\n"
                    "2. Sign in with Google (no credit card)\n"
                    "3. Click **Create API key** → copy\n"
                    "4. Paste above and hit **Save keys**"
                )
        with bcol2:
            if st.button("Save keys", type="primary", key="save_keys_btn", use_container_width=True):
                new_keys = {k: v.strip() for k, v in key_inputs.items()}
                save_keys(new_keys)
                st.success("Keys saved!")
                st.rerun()

# ── Bottom row: Theme | Data ───────────────────────────────────────────────────
col_left2, col_right2 = st.columns(2)

# ════════════ BOX 3 — Theme ════════════
THEME_PREVIEWS = [
    {"id": "Dark",         "name": "Dark",         "bg": "#0F1117", "surf": "#1A1D2E", "accent_c": "#6C63FF", "txt": "#E8EAED"},
    {"id": "Light",        "name": "Light",         "bg": "#F8F9FA", "surf": "#FFFFFF", "accent_c": "#4C6EF5", "txt": "#212529"},
    {"id": "Elegant Blue", "name": "Elegant Blue",  "bg": "#060D1A", "surf": "#0D1B2E", "accent_c": "#00A8FF", "txt": "#E0F0FF"},
    {"id": "Elegant Pink", "name": "Elegant Pink",  "bg": "#1A0A14", "surf": "#2D1220", "accent_c": "#E91E8C", "txt": "#FAE0EC"},
]

with col_left2:
    with st.container(border=True):
        _section_header("🎨 Theme", 50)

        current_theme = p.get("theme", "Dark")
        tc1, tc2 = st.columns(2)
        theme_col_map = [tc1, tc2, tc1, tc2]

        for i, th in enumerate(THEME_PREVIEWS):
            selected = th["id"] == current_theme
            shadow = f"3px 3px 0 {accent}" if selected else "none"
            bw = "2.5px" if selected else "1.5px"

            theme_col_map[i].markdown(f"""
            <div style="border:{bw} solid {border};border-radius:10px;
                        padding:8px;box-shadow:{shadow};margin-bottom:8px">
                <div style="height:56px;border-radius:6px;border:1.2px solid rgba(0,0,0,0.25);
                            background:{th['bg']};padding:6px;display:flex;gap:4px">
                    <div style="width:14px;background:{th['surf']};border-radius:3px;
                                border:1px solid rgba(0,0,0,0.2)"></div>
                    <div style="flex:1;display:flex;flex-direction:column;gap:3px">
                        <div style="height:6px;width:60%;background:{th['txt']};
                                    border-radius:99px;opacity:0.9"></div>
                        <div style="height:4px;width:85%;background:{th['txt']};
                                    border-radius:99px;opacity:0.5"></div>
                        <div style="height:4px;width:70%;background:{th['txt']};
                                    border-radius:99px;opacity:0.5"></div>
                        <div style="margin-top:auto;height:10px;width:28px;
                                    background:{th['accent_c']};border-radius:4px"></div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;
                            margin-top:6px;font-size:13px">
                    <span style="font-weight:{'700' if selected else '400'}">{th['name']}</span>
                    <span>{'●' if selected else '○'}</span>
                </div>
            </div>""", unsafe_allow_html=True)

            if theme_col_map[i].button(
                th["name"], key=f"theme_{th['id']}", use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                p["theme"] = th["id"]
                prog_utils.save(p)
                st.session_state.progress = p
                st.rerun()

        st.markdown(
            f'<div style="font-size:13px;color:{muted};margin-top:8px;margin-bottom:6px">'
            f'Code editor theme</div>',
            unsafe_allow_html=True,
        )
        code_themes = ["monokai", "github", "solarized"]
        current_code_theme = p.get("code_theme", "monokai")
        ct_cols = st.columns(3)
        for i, ct in enumerate(code_themes):
            sel = ct == current_code_theme
            if ct_cols[i].button(
                ct, key=f"ct_{ct}", use_container_width=True,
                type="primary" if sel else "secondary",
            ):
                p["code_theme"] = ct
                prog_utils.save(p)
                st.session_state.progress = p
                st.rerun()

# ════════════ BOX 4 — Data ════════════
with col_right2:
    with st.container(border=True):
        _section_header("💾 Data", 40)
        st.caption("Progress saved to `progress.json` in your project folder.")

        # Export
        progress_json = json.dumps(p, indent=2)
        st.download_button(
            label="⬇ Export progress",
            data=progress_json,
            file_name="iplearn_progress.json",
            mime="application/json",
            use_container_width=True,
            key="export_progress",
        )

        # Import
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "⬆ Import progress (.json)",
            type=["json"],
            key="import_progress",
        )
        if uploaded is not None:
            try:
                imported = json.loads(uploaded.read().decode("utf-8"))
                imported["theme"]     = p.get("theme", "Dark")
                imported["onboarded"] = True
                merged = {**prog_utils.DEFAULT, **imported}
                prog_utils.save(merged)
                st.session_state.progress = merged
                st.success("Progress imported!")
                st.rerun()
            except Exception as e:
                st.error(f"Could not read file: {e}")

        st.divider()
        st.markdown(
            f'<div style="font-size:14px;font-weight:600;color:{danger}">↺ Reset all</div>',
            unsafe_allow_html=True,
        )
        reset_confirm = st.checkbox(
            "I understand — delete all my progress",
            key="data_reset_confirm",
        )
        if reset_confirm:
            if st.button(
                "Reset everything",
                type="primary",
                key="data_reset_btn",
                use_container_width=True,
            ):
                keep = {
                    "name":          p.get("name", ""),
                    "onboarded":     True,
                    "theme":         p.get("theme", "Dark"),
                    "code_theme":    p.get("code_theme", "monokai"),
                    "daily_xp_goal": p.get("daily_xp_goal", 50),
                    "ai_provider":   p.get("ai_provider", "gemini"),
                    "goal":          p.get("goal", ""),
                }
                fresh = {**prog_utils.DEFAULT, **keep}
                prog_utils.save(fresh)
                st.session_state.progress = fresh
                st.success("All progress reset.")
                st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# Feedback from Student section
st.markdown(
    f'<div style="font-weight:700;font-size:18px;color:{text};margin-bottom:4px">'
    f'📬 Feedback from Student</div>',
    unsafe_allow_html=True,
)
entries = load_feedback()
if entries:
    st.markdown(
        f'<div style="font-size:13px;color:{muted};margin-bottom:8px">'
        f'{len(entries)} feedback entries</div>',
        unsafe_allow_html=True,
    )
    for entry in reversed(entries[-10:]):
        ts  = entry["timestamp"][:16].replace("T", " ")
        cat = entry["category"]
        pg  = entry["page"]
        msg = entry["message"]
        st.markdown(
            f'<div style="background:{surface};border:1.5px solid {border};'
            f'border-radius:8px;padding:10px 14px;margin-bottom:6px">'
            f'<span style="font-family:ui-monospace,monospace;font-size:12px;'
            f'color:{muted}">{ts}</span>'
            f'&nbsp; <strong style="color:{text}">{cat}</strong>'
            f' <span style="color:{muted}">on <em>{pg}</em></span><br>'
            + (f'<span style="font-size:13px;color:{text}">{msg}</span>'
               if msg and msg != "(no details)" else "")
            + f'</div>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        f'<div style="color:{muted};font-size:14px">No feedback yet.</div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# Recent Errors section
st.markdown(
    f'<div style="font-weight:700;font-size:18px;color:{text};margin-bottom:4px">'
    f'🐛 Recent Errors</div>',
    unsafe_allow_html=True,
)
errors = read_recent_errors(3)
if errors:
    for err in reversed(errors):
        with st.expander(err.split("\n")[0][:80] + "..."):
            st.code(err, language="text")
else:
    st.markdown(
        f'<div style="color:{muted};font-size:14px">No errors logged.</div>',
        unsafe_allow_html=True,
    )
