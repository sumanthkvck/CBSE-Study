"""
End-to-end Playwright tests for IP Learn.

The test suite auto-starts the Streamlit app on port 8502 for the session
and tears it down when done — no need to pre-start the server.

One-time setup (run once, outside pytest):
    playwright install chromium

Run:
    pytest tests/test_e2e.py -v --timeout=60
    pytest tests/test_e2e.py -v --timeout=60 --headed   # visible browser

Page URL slugs are derived from filenames (leading digit+underscore stripped):
    01_learn.py     → /learn
    02_mcq.py       → /mcq
    03_coding.py    → /coding
    04_ai_tutor.py  → /ai_tutor
    05_progress.py  → /progress
    06_settings.py  → /settings
"""
import re
import sys
import time
import subprocess
import requests
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

# ── Config ────────────────────────────────────────────────────────────────────
PORT        = 8502
BASE_URL    = f"http://localhost:{PORT}"
PROJECT_DIR = Path(__file__).parent.parent

SERVER_BOOT_TIMEOUT = 45   # seconds to wait for Streamlit to become ready
NAV_TIMEOUT  = 15_000      # ms for page.goto / networkidle
SHORT        = 8_000        # ms for element assertions


# ── Session-scoped server fixture ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def streamlit_server():
    """
    Start the Streamlit app on PORT for the entire test session.
    Yields the base URL string. Kills the process after all tests.
    """
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(PROJECT_DIR / "app" / "main.py"),
        "--server.port",             str(PORT),
        "--server.headless",         "true",
        "--server.runOnSave",        "false",
        "--server.fileWatcherType",  "none",
        "--browser.gatherUsageStats","false",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    health_url = f"{BASE_URL}/_stcore/health"
    deadline = time.time() + SERVER_BOOT_TIMEOUT
    ready = False
    while time.time() < deadline:
        try:
            r = requests.get(health_url, timeout=2)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    if not ready:
        proc.kill()
        out, _ = proc.communicate()
        pytest.fail(
            f"Streamlit server did not become ready within {SERVER_BOOT_TIMEOUT}s.\n"
            f"Output:\n{out.decode(errors='replace')[:2000]}"
        )

    yield BASE_URL

    proc.kill()
    proc.communicate()


# ── Helpers ───────────────────────────────────────────────────────────────────

def goto(page: Page, base: str, path: str = ""):
    """Navigate to base+path and wait for Streamlit to finish rendering."""
    page.goto(base + path, timeout=NAV_TIMEOUT)
    # Wait for Streamlit's status spinner to disappear
    try:
        page.wait_for_selector(
            '[data-testid="stStatusWidget"]',
            state="hidden",
            timeout=NAV_TIMEOUT,
        )
    except Exception:
        pass  # spinner may never appear — that's fine


def assert_no_exceptions(page: Page, path: str):
    count = page.locator('[data-testid="stException"]').count()
    assert count == 0, f"Streamlit exception found on {path}"


# ── Page load smoke tests ─────────────────────────────────────────────────────

def test_dashboard_loads(page: Page, streamlit_server):
    """Main dashboard loads without errors and shows sidebar."""
    goto(page, streamlit_server, "/")
    expect(page.locator('[data-testid="stSidebar"]')).to_be_visible(timeout=SHORT)
    expect(page.get_by_text("Your dashboard", exact=False)).to_be_visible(timeout=SHORT)
    assert_no_exceptions(page, "/")


def test_learn_page_loads(page: Page, streamlit_server):
    """Learn page shows chapter picker heading."""
    goto(page, streamlit_server, "/learn")
    expect(page.get_by_text("Pick a chapter", exact=False)).to_be_visible(timeout=SHORT)
    assert_no_exceptions(page, "/learn")


def test_learn_chapter_buttons_present(page: Page, streamlit_server):
    """Learn page has at least one chapter open button."""
    goto(page, streamlit_server, "/learn")
    btns = page.locator('button:has-text("Start →"), button:has-text("Continue →"), button:has-text("Review →")')
    # Wait for at least one button to render before counting
    expect(btns.first).to_be_visible(timeout=SHORT)
    assert btns.count() > 0, "No chapter open buttons found on Learn page"


def test_learn_chapter_opens(page: Page, streamlit_server):
    """Clicking a chapter button opens the two-panel topic viewer."""
    goto(page, streamlit_server, "/learn")
    btn = page.locator(
        'button:has-text("Start →"), button:has-text("Continue →"), button:has-text("Review →")'
    ).first
    btn.click()
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="hidden", timeout=NAV_TIMEOUT)
    except Exception:
        pass
    # Topic rail shows "ch.NN · topics" label
    expect(
        page.get_by_text(re.compile(r"ch\.\d{2} · topics", re.IGNORECASE))
    ).to_be_visible(timeout=SHORT)


def test_learn_explain_with_ai_button(page: Page, streamlit_server):
    """'Explain with AI' button is present after opening a chapter."""
    goto(page, streamlit_server, "/learn")
    btn = page.locator(
        'button:has-text("Start →"), button:has-text("Continue →"), button:has-text("Review →")'
    ).first
    btn.click()
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="hidden", timeout=NAV_TIMEOUT)
    except Exception:
        pass
    expect(page.locator('button:has-text("Explain with AI")')).to_be_visible(timeout=SHORT)


def test_mcq_page_loads(page: Page, streamlit_server):
    """MCQ page renders without errors and shows a chapter selector or question."""
    goto(page, streamlit_server, "/mcq")
    # Wait for Streamlit to populate stMain with actual content
    main = page.locator('[data-testid="stMain"]')
    expect(main).to_be_visible(timeout=SHORT)
    page.wait_for_function(
        "el => el.innerText.trim().length > 0",
        arg=main.element_handle(),
        timeout=SHORT,
    )
    main_text = main.inner_text()
    assert any(kw in main_text for kw in ("MCQ", "Practice", "Quiz", "Question", "chapter", "quiz")), \
        f"MCQ page missing expected content. Got: {main_text[:300]}"
    assert_no_exceptions(page, "/mcq")


def test_coding_page_loads(page: Page, streamlit_server):
    """Coding page shows 'Python challenges' heading."""
    goto(page, streamlit_server, "/coding")
    expect(page.get_by_text("Python challenges", exact=False)).to_be_visible(timeout=SHORT)
    assert_no_exceptions(page, "/coding")


def test_coding_challenge_list_non_empty(page: Page, streamlit_server):
    """Coding page has at least 5 'Open  →' challenge buttons."""
    goto(page, streamlit_server, "/coding")
    open_buttons = page.locator('button:has-text("Open  →")')
    # Wait for at least one button to render before counting
    expect(open_buttons.first).to_be_visible(timeout=SHORT)
    count = open_buttons.count()
    assert count >= 5, f"Expected >= 5 challenge buttons, got {count}"


def test_coding_solver_opens(page: Page, streamlit_server):
    """Opening the first challenge loads the split-panel solver with textarea and Run button."""
    goto(page, streamlit_server, "/coding")
    page.locator('button:has-text("Open  →")').first.click()
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="hidden", timeout=NAV_TIMEOUT)
    except Exception:
        pass
    # Use the Code textarea specifically (two textareas exist: Details + Code)
    expect(page.get_by_role("textbox", name="Code")).to_be_visible(timeout=SHORT)
    expect(page.locator('button:has-text("Run & test")')).to_be_visible(timeout=SHORT)


def test_ai_tutor_page_loads(page: Page, streamlit_server):
    """AI Tutor page loads without errors in launcher or integrated mode."""
    goto(page, streamlit_server, "/ai_tutor")
    main = page.locator('[data-testid="stMain"]')
    expect(main).to_be_visible(timeout=SHORT)
    page.wait_for_function(
        "el => el.innerText.trim().length > 0",
        arg=main.element_handle(),
        timeout=SHORT,
    )
    main_text = main.inner_text()
    assert any(kw in main_text for kw in ("Tutor", "AI", "Gemini", "chat", "Chat", "API", "Ask", "Class XI")), \
        f"AI Tutor page missing expected content. Got: {main_text[:300]}"
    assert_no_exceptions(page, "/ai_tutor")


def test_ai_tutor_input_present(page: Page, streamlit_server):
    """AI Tutor page shows either chat input (integrated) or question textarea (launcher)."""
    goto(page, streamlit_server, "/ai_tutor")
    # Wait for any recognisable interactive input to appear (with auto-wait)
    chat_input   = page.locator('[data-testid="stChatInput"]')
    question_box = page.get_by_label("Your question")          # launcher textarea
    gemini_link  = page.locator('a:has-text("Open in Gemini")')
    api_key_text = page.get_by_text("API key", exact=False)

    # At least one of these must become visible within SHORT ms
    any_found = False
    for loc in (chat_input, question_box, gemini_link, api_key_text):
        try:
            expect(loc.first).to_be_visible(timeout=SHORT)
            any_found = True
            break
        except Exception:
            pass
    assert any_found, "AI Tutor: no chat input, question textarea, Gemini link, or API key text found"


def test_progress_page_loads(page: Page, streamlit_server):
    """Progress page loads and shows XP or progress content."""
    goto(page, streamlit_server, "/progress")
    main = page.locator('[data-testid="stMain"]')
    expect(main).to_be_visible(timeout=SHORT)
    page.wait_for_function(
        "el => el.innerText.trim().length > 0",
        arg=main.element_handle(),
        timeout=SHORT,
    )
    main_text = main.inner_text()
    assert any(kw in main_text for kw in ("XP", "Progress", "Streak", "Chapter")), \
        f"Progress page missing expected content. Got: {main_text[:300]}"
    assert_no_exceptions(page, "/progress")


def test_settings_page_loads(page: Page, streamlit_server):
    """Settings page loads and shows API key section."""
    goto(page, streamlit_server, "/settings")
    main = page.locator('[data-testid="stMain"]')
    expect(main).to_be_visible(timeout=SHORT)
    page.wait_for_function(
        "el => el.innerText.trim().length > 0",
        arg=main.element_handle(),
        timeout=SHORT,
    )
    main_text = main.inner_text()
    assert any(kw in main_text for kw in ("API", "key", "Key", "Gemini", "Settings")), \
        f"Settings page missing expected content. Got: {main_text[:300]}"
    assert_no_exceptions(page, "/settings")


def test_sidebar_visible_on_all_pages(page: Page, streamlit_server):
    """Sidebar is visible on every page."""
    for path in ["/", "/learn", "/mcq", "/coding", "/ai_tutor", "/progress", "/settings"]:
        goto(page, streamlit_server, path)
        expect(page.locator('[data-testid="stSidebar"]')).to_be_visible(timeout=SHORT)


def test_no_import_errors_on_any_page(page: Page, streamlit_server):
    """No stException elements appear on any page."""
    for path in ["/", "/learn", "/mcq", "/coding", "/ai_tutor", "/progress", "/settings"]:
        goto(page, streamlit_server, path)
        assert_no_exceptions(page, path)
