# IP Learn — Class XI Informatics Practices

An interactive learning app for CBSE Class XI Informatics Practices (IP) students.
Built for 15-year-olds learning Python, databases, and computer science for the first time.

## Features
- Chapter-by-chapter lessons aligned to NCERT syllabus
- MCQ practice with instant feedback and explanations
- Python coding challenges with in-app code runner
- AI Tutor (free with Google Gemini, optional with Anthropic/OpenAI)
- XP + streak system to keep you motivated
- 4 color themes: Dark, Light, Elegant Pink, Elegant Blue

## Quick Start (Windows)
1. Install [Python 3.8+](https://python.org) — check "Add to PATH"
2. Download or clone this repo
3. Double-click `run.bat`
4. Browser opens at http://localhost:8501

## Quick Start (Mac/Linux)
```bash
pip3 install -r requirements.txt
streamlit run app/main.py
```

## AI Tutor Setup (optional but recommended)
The AI Tutor works for free with Google Gemini:
1. Get a free API key at https://aistudio.google.com/app/apikey
2. Copy `.env.example` to `.env`
3. Add your key: `GEMINI_API_KEY=your_key_here`

All MCQ, coding, and lesson features work without any API key.

## Chapters Covered
1. Computer System
2. Encoding Schemes and Number System
3. Emerging Trends (AI, IoT, Cloud, Blockchain)
4. Introduction to Problem Solving
5. Getting Started with Python
6. List Manipulation
7. Dictionary
8. Societal Impacts

## Screenshots
Coming soon — run the app to see it!

## Running Tests

### Unit tests (fast, no browser)
```bash
python -m pytest tests/ -m unit -v
```

### End-to-end tests (Playwright browser tests)
Install Chromium once after cloning:
```bash
playwright install chromium
```

Then run E2E tests (the app must NOT already be running on port 8502):
```bash
python -m pytest tests/test_e2e.py -v
```

To see the browser during tests (useful for debugging):
```bash
python -m pytest tests/test_e2e.py -v --headed
```

To run a single test:
```bash
python -m pytest tests/test_e2e.py::TestDashboard::test_dashboard_loads -v
```

## Contributing
Contributions welcome! This project is aimed at CBSE Class XI students and teachers in India.

- Report bugs or suggest improvements via GitHub Issues
- Content corrections (MCQs, explanations) are especially appreciated
- Please keep the language simple — target reader is a 15-year-old learning for the first time

## Syllabus Reference
This app covers the CBSE Class XI Informatics Practices (Code 065) syllabus.
Official syllabus and resources: [CBSE Academic](https://cbseacademic.nic.in/)

## License
MIT — free to use, share, and modify.
