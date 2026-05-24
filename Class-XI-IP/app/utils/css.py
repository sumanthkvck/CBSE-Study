import streamlit as st
from app.utils.themes import get_theme


def inject_theme_css(theme_name: str):
    """Inject CSS variables and all custom component classes."""
    t = get_theme(theme_name)
    st.markdown(f"""
    <style>
    :root {{
        --bg:       {t['bg']};
        --surface:  {t['surface']};
        --card:     {t['card']};
        --border:   {t['border']};
        --accent:   {t['accent']};
        --accent2:  {t['accent2']};
        --text:     {t['text']};
        --subtext:  {t['subtext']};
        --success:  {t['success']};
        --danger:   {t['danger']};
        --warn:     {t['warn']};
        --code-bg:  {t['code_bg']};
    }}

    /* Hide Streamlit's auto-generated multi-page nav — we use custom sidebar nav */
    [data-testid="stSidebarNav"] {{
        display: none !important;
    }}

    /* ── App shell ──────────────────────────────── */
    .stApp {{
        background-color: var(--bg);
        color: var(--text);
    }}
    section[data-testid="stSidebar"] {{
        background-color: {t['sidebar_bg']} !important;
    }}

    /* ── Sidebar text visibility ────────────────── */
    section[data-testid="stSidebar"] * {{
        color: {t['text']} !important;
    }}
    section[data-testid="stSidebar"] .stPageLink a {{
        color: {t['text']} !important;
        text-decoration: none;
        font-weight: 500;
    }}
    section[data-testid="stSidebar"] .stPageLink a:hover {{
        color: {t['accent']} !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {{
        color: {t['subtext']} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {{
        color: {t['text']} !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: {t['border']} !important;
        opacity: 1;
    }}
    /* Selectbox dropdown text */
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {{
        color: {t['text']} !important;
        background-color: {t['surface']} !important;
    }}

    /* ── Force theme text on ALL Streamlit native text elements ── */
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"] {{
        color: {t['text']};
    }}
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] em {{
        color: {t['text']};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {t['text']} !important;
    }}
    /* st.caption and helper text */
    [data-testid="stCaptionContainer"] p,
    small {{
        color: {t['subtext']} !important;
    }}
    /* st.divider */
    hr {{
        border-color: {t['border']} !important;
        opacity: 1 !important;
    }}
    /* Inline code inside st.markdown — ensure readable on all theme bgs */
    [data-testid="stMarkdownContainer"] code {{
        background-color: {t['code_bg']} !important;
        color: {t['subtext']} !important;
        padding: 1px 5px;
        border-radius: 4px;
    }}
    /* Form labels (text_input, selectbox, etc.) */
    [data-testid="stWidgetLabel"] p,
    .stTextInput label,
    .stSelectbox label,
    .stTextArea label,
    .stCheckbox label,
    .stFileUploader label {{
        color: {t['text']} !important;
    }}
    /* Input fields */
    .stTextInput input,
    .stTextArea textarea {{
        background-color: {t['surface']} !important;
        color: {t['text']} !important;
        border-color: {t['border']} !important;
    }}
    /* Selectbox in main content */
    div[data-baseweb="select"] * {{
        background-color: {t['surface']} !important;
        color: {t['text']} !important;
    }}
    /* Popover background */
    [data-testid="stPopover"] div[data-baseweb="popover"] {{
        background-color: {t['surface']} !important;
    }}
    /* stApp background with !important to beat Streamlit's own base styles */
    .stApp {{
        background-color: {t['bg']} !important;
        color: {t['text']} !important;
    }}

    /* ── Buttons ────────────────────────────────── */
    .stButton > button {{
        border-radius: 8px;
        border: 1.5px solid var(--border);
        background-color: var(--surface);
        color: var(--text);
        font-weight: 500;
        transition: border-color 0.15s, color 0.15s;
    }}
    .stButton > button:hover {{
        border-color: var(--accent);
        color: var(--accent);
    }}
    .stButton > button[kind="primary"] {{
        background-color: var(--accent);
        color: #fff;
        border-color: var(--accent);
        box-shadow: 3px 3px 0 rgba(0,0,0,0.25);
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: var(--accent);
        opacity: 0.9;
        color: #fff;
    }}

    /* ── Code / pre ─────────────────────────────── */
    code, pre {{
        background-color: var(--code-bg) !important;
        color: #ABB2BF !important;
        border-radius: 6px;
    }}

    /* ── Progress bars ──────────────────────────── */
    .progress-bar-outer {{
        background-color: var(--border);
        border-radius: 999px;
        height: 8px;
        width: 100%;
        overflow: hidden;
        margin: 4px 0;
    }}
    .progress-bar-inner {{
        background-color: var(--accent);
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s ease;
    }}
    .progress-bar-inner.done {{
        background-color: var(--success);
    }}

    /* ── XP badge ───────────────────────────────── */
    .xp-badge {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        border: 1.5px solid var(--border);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 13px;
        font-weight: 600;
        color: var(--text);
        background-color: var(--surface);
    }}

    /* ── Hero card ──────────────────────────────── */
    .hero-card {{
        background-color: var(--surface);
        border: 1.5px solid var(--border);
        border-radius: 14px;
        padding: 20px 22px;
    }}
    .hero-card.continue {{
        background-color: #FFF8E0;
        border: 2px solid var(--warn);
        color: var(--text);
    }}

    /* ── Chapter card ───────────────────────────── */
    .chapter-card {{
        background-color: var(--surface);
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 8px;
        transition: border-color 0.2s;
        min-height: 130px;
    }}
    .chapter-card:hover {{
        border-color: var(--accent);
    }}
    .chapter-card.doing {{
        background-color: #FFF8E0;
        border-color: var(--warn);
        color: var(--text);
    }}
    .chapter-card.locked {{
        opacity: 0.55;
        cursor: not-allowed;
    }}
    .chapter-card.locked:hover {{
        border-color: var(--border);
    }}

    /* ── Generic metric card ────────────────────── */
    .metric-card {{
        background-color: var(--card);
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }}

    /* ── Pill / badge ───────────────────────────── */
    .pill {{
        display: inline-block;
        border: 1.5px solid var(--border);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
        color: var(--text);
    }}
    .pill.accent {{
        background-color: var(--accent);
        border-color: var(--accent);
        color: #fff;
    }}
    .pill.success {{
        background-color: var(--success);
        border-color: var(--success);
        color: #fff;
    }}
    </style>
    """, unsafe_allow_html=True)
