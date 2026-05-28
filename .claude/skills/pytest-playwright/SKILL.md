# pytest-playwright Skill

You are a pytest-playwright expert for this project. Use this guide whenever the user asks you to write, run, fix, or explore Playwright tests.

## Project Data Flow

```
stories/*.md
  → python generate_test.py [--story <file>]
      → tests/test_*.py
          → python -m pytest [tests/test_<slug>.py] [-v --json-report --json-report-file=pytest-report.json]
              → python analyze/analyze_failures.py [--html]
                  → ai-analysis.json  +  ai-report.html
```

Full pipeline shortcut:
```bash
python pipeline.py [--story login.md] [--test test_login.py]
```

## Story Format

Story files live in `stories/<slug>.md`. The slug becomes the test function name.

```markdown
Title: <Descriptive title>

Base URL: https://example.com   ← optional if app is configured in test_config.yaml

As a user, I want to <goal>.

Acceptance criteria:
- Navigate to `/path`
- Fill in <field> `value`
- Click the <button>
- Expect <assertion>
```

`Base URL:` is optional. If omitted, `generate_test.py` reads the default from `test_config.yaml`
(`environments.<default_env>.base_url`). Include `Base URL:` only when the story targets a
**different** site than the repo default. Use relative paths (`/login`) in acceptance criteria —
the generator prepends the base URL.

## Test File Format

Tests live in `tests/test_<slug>.py`. One test function per file, named after the slug.

```python
from playwright.sync_api import Page, expect


def test_<slug>(page: Page):
    page.goto("https://example.com/path")
    page.get_by_label("Username").fill("tomsmith")
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_url("https://example.com/secure")
    expect(page.get_by_role("alert")).to_contain_text("You logged into a secure area!")
```

Rules:
- Always start with `from playwright.sync_api import Page, expect`
- Use the pytest `page: Page` fixture — never instantiate `sync_playwright()` in test files
- `base_url` is set in `browser_context_args` from `test_config.yaml` — you may use relative
  paths like `page.goto("/login")`, or full URLs; both work
- One `def test_<slug>(page: Page):` function, no class wrapper (unless using POM — see below)

## Commands Reference

```bash
# Generate test(s) from story file(s)
python generate_test.py                    # all stories
python generate_test.py --story login.md   # one story

# Run tests
python -m pytest                           # all tests
python -m pytest tests/test_login.py -v    # one test, verbose
python -m pytest --json-report --json-report-file=pytest-report.json  # with JSON output

# Analyze failures (requires pytest-report.json)
python analyze/analyze_failures.py         # JSON output only
python analyze/analyze_failures.py --html  # JSON + HTML report (auto-opens browser)

# Full pipeline
python pipeline.py
python pipeline.py --story login.md --test test_login.py

# UI server
uvicorn server.server:app --port 5173
```

All commands run from the project root. The virtualenv is at `.venv/`.

## Ad-hoc Exploration

When you need to quickly test a locator or explore a page without adding a permanent test, write a throwaway script to `/tmp/` and run it directly — do NOT place it in `tests/`:

```python
# /tmp/pw_scratch.py
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    page = browser.new_page()
    page.goto("https://the-internet.herokuapp.com/login")
    print(page.title())
    # inspect, screenshot, etc.
    browser.close()
```

```bash
python /tmp/pw_scratch.py
```

Clean up after: `rm /tmp/pw_scratch.py`

Use `headless=False` and `slow_mo=100` when exploring so you can see what's happening.

## Page Object Model (POM)

This project does not currently use POM. Introduce it only when a page is shared across multiple test files. Structure:

```
pages/
  login_page.py      # LoginPage class
tests/
  test_login.py      # imports LoginPage
  test_secure.py     # imports LoginPage
```

Page object pattern:
```python
# pages/login_page.py
from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.get_by_label("Username")
        self.password = page.get_by_label("Password")
        self.submit = page.get_by_role("button", name="Login")

    def login(self, username: str, password: str):
        self.page.goto("https://the-internet.herokuapp.com/login")
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()
```

Keep assertions in test files, not page objects.

## Locator Strategy

Prefer in this order:
1. `get_by_role("button", name="Submit")` — semantic, accessible
2. `get_by_label("Username")` — for inputs with labels
3. `get_by_text("Welcome")` — for visible text
4. `get_by_placeholder("Enter email")` — for inputs by placeholder
5. `locator("#id")` or `locator("[data-testid=foo]")` — only if semantic locators aren't available
6. Never use fragile CSS like `nth-child`, positional XPath, or long descendant selectors

## URL and Title Assertions

`expect(page).to_have_url()` and `expect(page).to_have_title()` each accept only a `str` (exact match) or `re.Pattern` (partial/regex match). Never pass a lambda or callable — it will raise a `TypeError`.

When an acceptance criterion says **"contains"** (e.g. "the page title contains 'Wikipedia'"), translate that to `re.compile()` — never a lambda:

```python
import re

expect(page).to_have_url(re.compile(r"/status_codes/200"))
expect(page).to_have_title(re.compile(r"Wikipedia"))
```

## "Page Loads Successfully"

When a story criterion says "the page loads successfully" without specifying a URL, assert the page title or a key visible element — never invent a URL assertion:

```python
expect(page).to_have_title(re.compile(r"HDMI", re.IGNORECASE))  # title proves page loaded
expect(page.locator("h1")).to_be_visible()                       # or a key element
```

A URL assertion confirms navigation, not page load. Only add `to_have_url()` when the story explicitly states what the URL should be.

## Wait Strategies

Never use `page.wait_for_timeout()` (hardcoded sleep). Use:

```python
page.wait_for_url("**/secure")          # after navigation
page.wait_for_load_state("networkidle") # after heavy page loads
expect(locator).to_be_visible()         # auto-waits up to default timeout
expect(locator).to_contain_text("...")  # auto-waits
```

Playwright's `expect()` assertions auto-retry for up to 5 seconds by default — lean on them.

## File Naming Convention

| Story file | Test file | Test function |
|---|---|---|
| `stories/login.md` | `tests/test_login.py` | `def test_login(page: Page):` |
| `stories/add_remove_elements.md` | `tests/test_add_remove_elements.py` | `def test_add_remove_elements(page: Page):` |

The slug is always the story filename stem, snake_cased.

## Workflow for New Tests

1. Write `stories/<slug>.md` with Title, Base URL, and acceptance criteria
2. Run `python generate_test.py --story <slug>.md` to generate the test
3. Review `tests/test_<slug>.py` — edit locators or assertions if needed
4. Run `python -m pytest tests/test_<slug>.py -v` to verify
5. If it fails, run `python analyze/analyze_failures.py --html` for AI diagnosis
