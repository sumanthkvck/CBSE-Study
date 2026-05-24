import streamlit as st
from app.utils.themes import theme_names
from app.utils import feedback as fb_utils
from app.utils.env import is_cloud

def render_sidebar(progress_data: dict) -> str:
    """
    Render the sidebar: logo, nav links, XP/streak, theme picker, feedback widget.
    Returns the selected theme name.
    """
    with st.sidebar:
        # Logo
        st.markdown("## ⚡ IP Learn")
        st.caption("Class XI · KIPS · CBSE")
        if is_cloud():
            st.caption("🌐 Demo mode")
        st.divider()

        # Navigation
        st.markdown("**Navigate**")
        st.page_link("main.py",                        label="🏠  Dashboard")
        st.page_link("pages/01_learn.py",              label="📚  Learn")
        st.page_link("pages/02_mcq.py",                label="📝  Practice MCQ")
        st.page_link("pages/03_coding.py",             label="💻  Coding Challenges")
        st.page_link("pages/04_ai_tutor.py",           label="🤖  AI Tutor")
        st.page_link("pages/05_progress.py",           label="📊  My Progress")
        st.page_link("pages/06_settings.py",           label="⚙️  Settings")

        st.divider()

        # XP and streak
        xp     = progress_data.get("xp", 0)
        streak = progress_data.get("streak", 0)
        st.markdown(f"⚡ **{xp} XP**")
        st.markdown(f"🔥 **{streak}** day streak")

        st.divider()

        # Theme picker
        current_theme = progress_data.get("theme", "Dark")
        themes        = theme_names()
        idx           = themes.index(current_theme) if current_theme in themes else 0
        chosen = st.selectbox("🎨 Theme", themes, index=idx, key="theme_selector")

        # Save theme immediately when changed — triggers a rerun so CSS re-injects
        if chosen != current_theme:
            from app.utils import progress as prog_utils
            progress_data["theme"] = chosen          # update the dict in-place (session state ref)
            prog_utils.save(progress_data)
            st.rerun()

        st.divider()

        # Feedback widget — always visible, always simple
        with st.popover("💬 Send feedback to Dad"):
            st.caption("Found a bug? Something confusing? Tell me!")
            current_page = st.session_state.get("_current_page", "unknown")
            category = st.selectbox(
                "What is it?",
                ["🐛 Something broke", "😕 This is confusing", "💡 Suggestion", "👍 I like this"],
                key="fb_category",
            )
            message = st.text_area("Details (optional)", key="fb_message", height=80)
            if st.button("Send", key="fb_send", type="primary"):
                fb_utils.save_feedback(
                    page=current_page,
                    message=message or "(no details)",
                    category=category,
                )
                st.success("Thanks! Dad will see this.")
                st.session_state["fb_message"] = ""

        return chosen
