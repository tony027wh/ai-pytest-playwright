# AI pytest-Playwright Test Lab

An end-to-end AI-powered test automation pipeline that turns plain-English user stories into running Playwright tests, analyzes failures with Claude, and produces a styled HTML report.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Workflow: Run All Tests](#workflow-run-all-tests)
5. [Workflow: Add a New Story and Test It](#workflow-add-a-new-story-and-test-it)
6. [Individual Commands Reference](#individual-commands-reference)
7. [UI Dashboard](#ui-dashboard)
8. [Claude Code Skill](#claude-code-skill)
9. [How AI Analysis Works](#how-ai-analysis-works)
10. [Cross-Repo Utility Design](#cross-repo-utility-design)
11. [Roadmap](#roadmap)

---

## Tech Stack

- **Python 3.13+**
- **pytest + pytest-playwright**
- **Claude Code CLI** — no API keys needed, uses your Claude Code subscription
- **FastAPI** for the local UI server
- **Dark-mode HTML dashboard** with external CSS

---

## Project Structure

```
ai-pytest-playwright/
│
├── stories/                       # Plain-English test specifications (.md)
├── tests/                         # Auto-generated pytest-playwright tests
│   └── .ai-backups/               # Backups created before AI fixes
│
├── shared_utils/                  # Reusable utility library (copy to any repo)
│   ├── adapters/
│   │   └── base.py                # AppAdapter ABC — abstract interface for per-repo behavior
│   └── core/
│       ├── config_loader.py       # Loads test_config.yaml, resolves ${ENV_VAR:-default}
│       ├── retry.py               # retry() and wait_for() helpers
│       └── assertions.py         # SoftAssertions — collect failures, raise at end
│
├── adapters/
│   └── the_internet_adapter.py   # Concrete AppAdapter for this repo's target app
│
├── analyze/
│   └── analyze_failures.py       # AI failure analysis engine
├── utils/
│   ├── claude_client.py          # Claude CLI subprocess helpers
│   └── test_helpers.py           # Shared test utilities
├── server/
│   └── server.py                 # FastAPI server
├── ui/                           # Frontend (index.html, ui.js, ui.css, modules/)
│
├── test_config.yaml              # Repo-level config: environments, browser, auth, routes
├── generate_test.py              # Converts stories → pytest tests
├── pipeline.py                   # Full pipeline orchestrator
├── conftest.py                   # pytest + Playwright fixtures (config-driven)
├── pytest.ini                    # pytest configuration
└── requirements.txt
```

**Data flow:**
```
test_config.yaml  ←─ conftest.py  ←─ adapters/the_internet_adapter.py
                                        │
stories/*.md                            │ base_url, browser settings, auth
  → generate_test.py                    │
      → tests/test_*.py ───────────────→ pytest  →  pytest-report.json  +  playwright-report/
                                              → analyze_failures.py
                                                  → ai-analysis.json  +  ai-report.html
```

---

## Installation

```bash
git clone https://github.com/andrewtdinh/ai-pytest-playwright.git
cd ai-pytest-playwright
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install
```

No API keys required. The project uses the **Claude Code CLI** (`claude` command) bundled with your Claude Code subscription. [Get Claude Code here](https://claude.ai/code) if you haven't installed it.

---

## Workflow: Run All Tests

Use this when you want to run the entire suite end-to-end.

**Step 1 — Run the full pipeline**

```bash
python pipeline.py
```

This does four things in sequence:
1. Generates pytest tests from every story in `stories/`
2. Runs the full pytest suite
3. Analyzes any failures with AI
4. Builds and opens `ai-report.html` in your browser

**Step 2 — Review the results**

- `ai-report.html` — AI dashboard: plain-English explanations, root causes, fix suggestions, flakiness tips
- `playwright-report/` — Traditional pytest-html report with screenshots
- `pytest-report.json` — Raw machine-readable output

---

## Workflow: Add a New Story and Test It

Use this when you've written a new story and only want to generate and run that one test.

**Step 1 — Write your story**

Create `stories/<slug>.md`. The filename stem becomes the test function name.

```markdown
Title: Login - valid credentials

As a user, I want to log in with valid credentials so I can access the secure area.

Acceptance criteria:
- Navigate to `/login`
- Fill in username `tomsmith`
- Fill in password `SuperSecretPassword!`
- Click the Login button
- Expect redirect to `/secure`
- Expect the success flash message to contain: `You logged into a secure area!`
```

Notes:
- **`Base URL:` is optional.** If omitted, `generate_test.py` uses the default from `test_config.yaml` (`environments.<default_env>.base_url`). Only include `Base URL:` when the story targets a *different* site than the repo default.
- Use relative paths in acceptance criteria (`/login`, not the full URL).
- The slug (filename stem) must be snake_case: `add_remove_elements.md` → `test_add_remove_elements.py`.

**Step 2 — Generate the test**

```bash
python generate_test.py --story <slug>.md
```

Example:
```bash
python generate_test.py --story login.md
```

This creates `tests/test_login.py`. Review it and adjust any locators if needed.

**Step 3 — Run only that test**

```bash
python -m pytest tests/test_<slug>.py -v
```

**Step 4 — If it fails, get AI analysis**

```bash
python -m pytest tests/test_login.py -v --json-report --json-report-file=pytest-report.json
python analyze/analyze_failures.py --html
```

Or use the pipeline shortcut for steps 2–4 in one command:

```bash
python pipeline.py --story login.md --test test_login.py
```

---

## Individual Commands Reference

```bash
# Generate tests
python generate_test.py                          # all stories
python generate_test.py --story login.md         # one story

# Run tests
python -m pytest                                 # all tests
python -m pytest tests/test_login.py -v          # one test
python -m pytest --json-report --json-report-file=pytest-report.json  # with JSON output

# Analyze failures (requires pytest-report.json)
python analyze/analyze_failures.py               # JSON output only
python analyze/analyze_failures.py --html        # JSON + HTML report (auto-opens)

# Full pipeline
python pipeline.py                               # all stories + all tests
python pipeline.py --story login.md --test test_login.py  # one story + one test

# UI server
uvicorn server.server:app --port 5173
```

---

## UI Dashboard

```bash
uvicorn server.server:app --port 5173
```

Open `http://localhost:5173`.

**Run Bar** — trigger the full pipeline or individual steps (Generate / Run Tests / Analyze) with a live status chip.

**Editor** — write or edit stories and tests with validation, upload up to 5 stories at once, or use the AI Story Assistant wizard to build a story from requirements and expected outcomes.

**Saved Stories / Generated Tests** — browse, edit, delete, or run individual stories or tests from the sidebar.

**Run Console** — step-by-step progress (Validate → Save → Generate → Run → Analyze → Report), live logs, and a **Fix with AI** button on failed tests that auto-applies a Claude-generated fix, creates a backup in `tests/.ai-backups/`, re-runs the test, and shows a fix summary.

**Report Tabs** — embedded AI analysis report and traditional Playwright HTML report with screenshots, side by side.

---

## Claude Code Skill

This repo ships a Claude Code skill at `.claude/skills/pytest-playwright/SKILL.md`.

When working inside Claude Code, type:

```
/pytest-playwright
```

This loads the skill and gives Claude full context about this project: the story format, test file conventions, all available commands, locator best practices, wait strategies, POM guidance, and an ad-hoc exploration pattern for quick locator debugging.

**When to use it:**
- Writing a new story or test file
- Debugging a failing test
- Asking Claude to explain a locator or wait strategy
- Getting help with the full pipeline

---

## How AI Analysis Works

After pytest runs, failure metadata is passed to Claude via the CLI:

- Error message and full traceback
- Test node ID
- stdout/stderr logs
- The original user story (for context about intent)

Claude returns a structured HTML snippet for each failure containing:

1. **Plain-English Explanation** — why it likely failed, grounded in the real behavior of the page under test
2. **Probable Root Causes** — 2–3 concrete technical causes
3. **Suggested Test Fixes** — specific pytest-playwright code improvements
4. **Flakiness Mitigation** — ways to reduce intermittent failures

Output is written to `ai-analysis.json` (structured data) and `ai-report.html` (styled dashboard).

---

## Cross-Repo Utility Design

`shared_utils/` is a portable utility library built to work across multiple repos targeting different applications.

### How it works

`test_config.yaml` (one per repo) declares the target app's properties:

```yaml
app:
  name: "my-app"
  default_env: "${TEST_ENV:-staging}"

environments:
  staging:
    base_url: "https://staging.my-app.com"
  production:
    base_url: "https://my-app.com"

browser:
  headless: true
  viewport: {width: 1280, height: 720}
  slow_mo: 0

auth:
  strategy: "form"
  state_file: ".playwright/.auth/user.json"
  credentials:
    username: "${TEST_USERNAME}"
    password: "${TEST_PASSWORD}"

routes:
  login: "/login"
  dashboard: "/dashboard"
```

`conftest.py` feeds the config into pytest-playwright's built-in fixture hooks (`browser_context_args`, `browser_type_launch_args`), so `base_url`, viewport, and browser settings flow into every test automatically — no duplication in test files or stories.

### Adding this to another repo

1. Copy `shared_utils/` into the new repo.
2. Write `adapters/my_app_adapter.py` implementing the three required methods:

```python
from playwright.sync_api import Page
from shared_utils.adapters.base import AppAdapter

class MyAppAdapter(AppAdapter):
    def login(self, page: Page) -> None:
        creds = self.config["auth"]["credentials"]
        page.goto(self.base_url() + self.route("login"))
        page.get_by_label("Email").fill(creds["username"])
        page.get_by_label("Password").fill(creds["password"])
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url("**/dashboard")

    def seed_data(self) -> dict:
        # create test fixtures via API or DB; return refs for cleanup
        return {}

    def cleanup_data(self, data: dict) -> None:
        pass
```

3. Write `test_config.yaml` for the new repo.
4. In `conftest.py`, return your adapter from `app_adapter` — everything else is inherited:

```python
import pytest
from adapters.my_app_adapter import MyAppAdapter
from shared_utils.core.config_loader import load_config

@pytest.fixture(scope="session")
def repo_config():
    return load_config("test_config.yaml")

@pytest.fixture(scope="session")
def app_adapter(repo_config):
    return MyAppAdapter(repo_config)

# browser_type_launch_args, browser_context_args, auth_state,
# and authenticated_page fixtures follow the same pattern as this repo's conftest.py
```

### Shared utilities

| Module | What it provides |
|---|---|
| `shared_utils.adapters.base.AppAdapter` | Abstract base: `login`, `seed_data`, `cleanup_data` (required); `after_navigation`, `setup_context`, `on_auth_failure` (overridable); `base_url`, `route`, `navigate_to` (config-derived) |
| `shared_utils.core.config_loader.load_config` | Loads `test_config.yaml` and resolves `${VAR:-default}` from environment |
| `shared_utils.core.retry.retry` | Retry a callable N times with delay |
| `shared_utils.core.retry.wait_for` | Poll a condition until True or timeout |
| `shared_utils.core.assertions.SoftAssertions` | Collect multiple failures and raise them all at once |

---

## Roadmap

- Multi-story batch generation
- Test-to-story reverse engineering
- Flaky test scoring over time
- Hit-map UI of frequent failures
- CI pipeline integration
- Slack/Teams bot that posts AI insights
