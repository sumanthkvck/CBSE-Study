# IP Learn — Class XI Informatics Practices

## What This Is
An interactive learning app for CBSE Class XI Informatics Practices (code 065) students in India.
Target user: 15-year-olds with zero programming background.
Built with Streamlit. Distributed via `run.bat` (Windows one-click) + Streamlit Cloud (share-a-URL).

## Tech Stack
- Python 3.8+ / Streamlit (local web app, opens in browser)
- AI: Google Gemini 1.5 Flash (free default, no credit card needed)
  Fallback chain: GEMINI_API_KEY → ANTHROPIC_API_KEY → OPENAI_API_KEY → offline mode
- Progress: JSON file (`progress.json`) — no database needed
- Content: JSON files in `app/content/` — MCQs, coding challenges per chapter
- Packaging: `run.bat` / `run.sh` launcher + `requirements.txt`

## Reference Textbook
KIPS Informatics Practices Class XI (Code 065) by Chetna Goyal, Kips Learning Pvt. Ltd., 2023. ISBN: 978-93-92643-75-0

## CBSE Class XI IP Syllabus — 10 Chapters (KIPS structure)
1. Introduction to Computer System (Unit I, pp. 1–23)
2. Programming with Python (Unit II, pp. 24–34)
3. Python Basics (Unit II, pp. 35–61)
4. Data Types and Operators (Unit II, pp. 62–96)
5. Control Flow Statements (Unit II, pp. 97–118)
6. List Manipulation (Unit II, pp. 119–143)
7. Python Dictionary (Unit II, pp. 144–166)
8. Database Concepts (Unit III, pp. 167–181)
9. Structured Query Language (Unit III, pp. 182–210)
10. Emerging Trends in Technology (Unit IV, pp. 211–241)

## Project Structure (after pipeline completes)
```
app/
  main.py               # Streamlit entry point (streamlit run app/main.py)
  pages/
    01_learn.py         # Chapter content viewer
    02_mcq.py           # MCQ practice
    03_coding.py        # Python coding challenges
    04_ai_tutor.py      # AI chat tutor
    05_progress.py      # Progress & stats
    06_settings.py      # API keys, preferences
  components/
    sidebar.py          # Navigation + XP display
    code_runner.py      # Sandboxed Python executor
    ai_block.py         # AI response renderer
  ai/
    provider.py         # Multi-provider AI abstraction
  content/
    ch01_computer_system.json
    ch02_programming_python.json
    ch03_python_basics.json
    ch04_data_types_operators.json
    ch05_control_flow.json
    ch06_lists.json
    ch07_dictionary.json
    ch08_database_concepts.json
    ch09_sql.json
    ch10_emerging_trends.json
  utils/
    progress.py         # XP, streaks, persistence
    qr_links.py         # DIKSHA QR code URL map
pipeline/               # Claude pipeline prompt files
  00_foundation.md
  01_content_data.md
  ...
tests/
  test_app.py
  test_content.py
  test_ai_provider.py
Textbook/               # KIPS PDF (not committed to git — place book here for reference)
run.bat                 # Windows: check Python, install deps, launch app
run.sh                  # Mac/Linux launcher
requirements.txt
LICENSE                 # MIT
.env.example            # Template: GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
.gitignore
```

## Pipeline Workflow
- Entry point: `python run_pipeline.py`
- Resumes from `.pipeline_state.json` if interrupted
- Each phase = one prompt file in `pipeline/`, run via `claude_runner.py`
- After each phase: git commit automatically
- Review gates defined in `GATES` dict in `run_pipeline.py`

```bash
python run_pipeline.py            # run all, resume if interrupted
python run_pipeline.py --only N   # run single phase N
python run_pipeline.py --start N  # resume from phase N
python run_pipeline.py --no-gates # fully autonomous, skip human gates
python run_pipeline.py --log      # write logs to logs/
```

## UI Conventions (Streamlit)
- Dark theme: bg `#0F1117`, surface `#1A1D2E`, accent `#6C63FF`, success `#2ED573`
- Sidebar: navigation + XP/streak display only — no main content in sidebar
- No `st.expander` for primary content
- Friendly tone: encouraging messages, celebrate correct answers with XP
- Indian context in examples where natural (cricket scores, school grades, etc.)

## Content Rules — IMPORTANT
- Never copy textbook text verbatim (copyright)
- Generate original explanations, examples, and questions aligned to the KIPS syllabus
- Each chapter JSON must have: `title`, `topics`, `summary`, `mcqs` (min 8), `key_concepts` (min 6)
- MCQ format: `id` (unique, e.g. "ch01_q001"), `question`, `options` (exactly 4), `correct_index` (0-3), `explanation`, `difficulty` (Easy/Medium/Hard)
- Coding format: `id`, `title`, `description`, `starter_code`, `expected_output`, `hint`, `test_cases`
- Coding challenges: required for ch02-ch07, ch09 only; ch01, ch08, ch10 have `"coding_challenges": []`
- Keep language simple — assume zero prior knowledge for Ch 1-4, building knowledge for Ch 5-9

## AI Provider Config (`app/ai/provider.py`)
- Reads from `.env` file (or env vars)
- Settings page lets students enter their own key in-app
- Keys stored in `~/.iplearn_keys` (not in project dir, never committed)
- If no key: all non-AI features work; AI Tutor shows "Set up a free API key" guide

## CBSE Study Material Links (`app/utils/qr_links.py`)
Each chapter links to CBSE/DIKSHA study material.
These are in `qr_links.py` as `CHAPTER_LINKS` dict `{chapter_num: {"url": ..., "label": ...}}`.
Display them in the chapter viewer as "Open CBSE study material on DIKSHA →" link.

## Common Commands
```bash
streamlit run app/main.py          # run the app (localhost:8501)
python run_pipeline.py             # run the build pipeline
python -m pytest tests/ -v         # run test suite
python -m pytest tests/ -k "mcq"   # run specific tests
```

## Distribution (for students)
1. Students download the project as a ZIP from GitHub
2. Double-click `run.bat` (Windows) — it installs deps and opens browser
3. Or visit Streamlit Cloud URL (no install needed)
Exe packaging (PyInstaller) is NOT planned — Streamlit + launcher is sufficient.

## Git Conventions
- `feat:` new feature/content, `fix:` bug fix, `pipeline:` pipeline prompt changes
- `content:` adding MCQs/challenges, `docs:` README/docs only
- Commit after each pipeline phase completes
- `Textbook/` is in `.gitignore` — PDFs are not committed
