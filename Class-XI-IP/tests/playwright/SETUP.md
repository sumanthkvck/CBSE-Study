# Playwright Setup

## One-time browser install

```bash
playwright install chromium
```

## Run smoke tests (app auto-starts on port 8502)

```bash
pytest tests/test_e2e.py -v --timeout=60
```

The test session fixture starts Streamlit on port 8502 automatically —
you do not need to start the app separately.

## Run in headed mode (visible browser, useful for debugging)

```bash
pytest tests/test_e2e.py -v --timeout=60 --headed
```

## Run only unit tests (no browser needed)

```bash
pytest tests/ -m unit -v
```

## Run only e2e tests

```bash
pytest tests/ -m e2e -v --timeout=60
```

## Page URL slugs

Streamlit derives URL slugs from filenames (stripping the leading `NN_` prefix):

| File                   | URL slug     |
|------------------------|--------------|
| `app/main.py`          | `/`          |
| `pages/01_learn.py`    | `/learn`     |
| `pages/02_mcq.py`      | `/mcq`       |
| `pages/03_coding.py`   | `/coding`    |
| `pages/04_ai_tutor.py` | `/ai_tutor`  |
| `pages/05_progress.py` | `/progress`  |
| `pages/06_settings.py` | `/settings`  |

If a test fails with a 404 or empty page, check that the URL slug matches
the current filename by running the app and inspecting the browser address bar.
