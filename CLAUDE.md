# ai-pytest-playwright

AI-powered pytest-playwright test automation framework. User stories in markdown → Claude generates Python tests → pytest runs them → AI analyzes failures.

## Commands

```bash
# Full pipeline (generate + test + analyze + HTML report)
python pipeline.py

# Individual steps
python generate_test.py                    # Generate tests from all stories
python generate_test.py --story login.md   # Generate test for one story
python -m pytest                           # Run all tests
python analyze/analyze_failures.py         # AI analysis (JSON only)
python analyze/analyze_failures.py --html  # AI analysis + HTML report

# UI server (http://localhost:5173)
uvicorn server.server:app --port 5173
```

## Architecture

### Data flow
```
stories/*.md
    → generate_test.py (claude -p subprocess)
        → tests/test_*.py
            → pytest (pytest-report.json + playwright-report/)
                → analyze/analyze_failures.py
                    → ai-analysis.json + ai-report.html
```

### Story format
Plain English `.md` files in `stories/`. The filename stem becomes the test slug:
- `stories/login.md` → `tests/test_login.py` → `def test_login(page: Page):`

```markdown
Title: Login - valid credentials

Base URL: https://the-internet.herokuapp.com

As a user, I want to log in with valid credentials.

Acceptance criteria:
- Navigate to `/login`
- Fill in username `tomsmith`
- Fill in password `SuperSecretPassword!`
- Click the Login button
- Expect redirect to `/secure`
```

### pytest-json-report format
`analyze_failures.py` reads `pytest-report.json`. Test nodeids have format:
`tests/test_login.py::test_login`

The slug is extracted by stripping `test_` prefix from the filename stem:
`test_login.py` → `login` → loads `stories/login.md` for context.

### Test file naming
- Story: `stories/add_remove_elements.md`
- Test file: `tests/test_add_remove_elements.py`
- Test function: `def test_add_remove_elements(page: Page):`

### Reports
- `pytest-report.json` — machine-readable pytest output (input to analyzer)
- `playwright-report/` — pytest-html traditional report (iframed in UI)
- `ai-analysis.json` — structured AI analysis per failure
- `ai-report.html` + `ai-report.css` — beautiful AI failure dashboard

### Server
FastAPI server mirrors the Node HTTP server API exactly.
All `/api/*` paths are identical so the UI works unchanged.

Test file backups before AI fixes are stored in `tests/.ai-backups/`.

## Dependencies

```
pytest
pytest-playwright
pytest-json-report
pytest-html
fastapi
uvicorn[standard]
python-dotenv
```

Install:
```bash
pip install -r requirements.txt
playwright install
```
