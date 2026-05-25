# 🚀 AI pytest-Playwright Test Lab

An end-to-end **AI-powered test automation pipeline** that:

✔️ **Generates pytest-playwright tests** from plain-English user stories

✔️ **Runs your pytest suite**

✔️ **Analyzes failed tests using AI**, producing explanations, root causes, fix suggestions, and flakiness tips

✔️ **Builds a beautifully styled HTML dashboard** of all AI results
✔️ **Embedded UI reports** (AI analysis + Playwright HTML report with screenshots)
✔️ **Fix with AI** to auto-apply test repairs and re-run

✔️ **One-command workflow** using `python pipeline.py`

---

## 📸 Demo Overview

This workflow turns simple input like:

**`stories/login.md`**

```
As a user, I want to log in with valid credentials so I can access my dashboard.

Acceptance criteria:
- Navigate to /login
- Fill in username tomsmith
- Fill in password SuperSecretPassword!
- Click the Login button
- Expect redirect to /secure
```

Into:

* A generated pytest-playwright test
* A full run
* AI failure analysis
* A glowing, animated HTML dashboard like this:

**`ai-report.html`** (auto-opens):

* Plain English explanation
* Root cause analysis
* Suggested test fixes
* Flakiness mitigation
* Styled cards, badges, gradients, animations

---

## 🔧 Tech Stack

* **Python 3.13+**
* **pytest + pytest-playwright**
* **Claude Code CLI** (no API keys needed — uses your Claude Code subscription)
* **FastAPI** server for the UI
* **Custom HTML reporting with external CSS**
* **Dark-mode dashboard UI**

---

## 📂 Project Structure

```
ai-pytest-playwright/
│
├── stories/
│   └── login.md               # Your natural language test cases
│
├── tests/
│   └── test_login.py          # Auto-generated pytest-playwright test
│   └── .ai-backups/           # AI fix backups (hidden in UI)
│
├── analyze/
│   └── analyze_failures.py    # AI engine (JSON + HTML dashboard)
│
├── utils/
│   ├── claude_client.py       # Claude CLI subprocess helpers
│   └── test_helpers.py        # Shared test utilities
│
├── server/
│   └── server.py              # FastAPI server (mirrors JS API exactly)
│
├── ui/                        # Frontend (same UI as JS version)
│   ├── index.html
│   ├── ui.js / ui.css
│   └── modules/               # Editor, run console, AI wizard, etc.
│
├── ai-analysis.json            # AI output (JSON)
├── ai-report.html              # Human-friendly HTML dashboard
├── ai-report.css               # Dashboard styling
├── playwright-report/          # pytest-html report (screenshots)
├── pytest-report.json          # Machine-readable pytest output
│
├── generate_test.py            # Converts stories → pytest tests
├── pipeline.py                 # Full pipeline orchestrator
├── conftest.py                 # pytest + Playwright fixtures
├── pytest.ini                  # pytest configuration
├── requirements.txt            # Python dependencies
└── README.md                   # (this file)
```

---

## ⚙️ Installation

```bash
git clone https://github.com/andrewtdinh/ai-pytest-playwright.git
cd ai-pytest-playwright
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

**Note:** No API keys needed! The project uses the **Claude Code CLI** (`claude` command) which is included with Claude Code. If you haven't installed Claude Code yet, [get it here](https://claude.ai/code).

---

## 🧠 One-Command Workflow

Run this to:

1. Generate tests from your stories
2. Run all pytest-playwright tests
3. Analyze failures using AI
4. Build & open the HTML dashboard

```bash
python pipeline.py
```

---

## 👉 Individual Commands (Optional)
## 🧭 UI Dashboard (Local)

Run the UI:

```bash
uvicorn server.server:app --port 5173
```

Open `http://localhost:5173`.

### What you can do in the UI

**Run Bar**
- Run full pipeline or individual steps (Generate / Run Tests / Analyze)
- Live status chip: Idle / Running / Failed / Passed

**Editor**
- Single editor for stories and tests (toggle mode)
- Story validation required before save
- Upload up to 5 stories at a time
- AI Story Assistant (wizard) builds a story from requirements + optional selectors/steps + expected outcome

**Saved Stories**
- Refresh, delete all, edit
- Per‑story Generate button (creates tests just for that story)

**Generated Tests**
- Refresh, delete all, edit
- Per‑test Run button (runs only that test)

**Run Console**
- Stepper: Validate → Save → Generate → Run → Analyze → Report
- Live logs, inline errors, copy stdout/stderr
- "Open report" CTA when available
- Report tabs:
  - AI Analysis (embedded `ai-report.html`)
  - Traditional Report (embedded Playwright HTML report)
- Fix with AI button for failed tests:
  - Auto-applies changes, re-runs the test, and shows a fix summary

**Safety / UX**
- Custom confirm modal for deletes
- Buttons disabled during runs

### AI Story Assistant

The UI includes an AI Story Assistant wizard that helps craft stories in a structured format:

- Collects requirements, selectors/UI elements, path/steps, and expected outcome
- Generates a story that fits the editor format
- Inserts the story directly into the editor

Use it when you want consistent story structure or faster authoring.

### Fix with AI

When a test fails, the Report section lists failed tests with a **Fix with AI** button.

What it does:

- Sends full context to Claude via the CLI (test file, stdout/stderr, error context, related story)
- Auto-applies the updated test file
- Creates a backup in `tests/.ai-backups/`
- Re-runs the fixed test and shows a short fix summary in the Run Console

No API keys required — uses Claude Code CLI.


### Generate tests from your stories

```bash
python generate_test.py
# or for a single story:
python generate_test.py --story login.md
```

Creates pytest test files under `tests/`.

---

### Run the pytest-playwright suite

```bash
python -m pytest
```

Saves `pytest-report.json`.
Also writes the Playwright HTML report to `playwright-report/`.

---

### Analyze failures using AI (JSON only)

```bash
python analyze/analyze_failures.py
```

Saves structured output in `ai-analysis.json`.

---

### Build + open the HTML dashboard

```bash
python analyze/analyze_failures.py --html
```

Auto-opens `ai-report.html` in your browser.
Also writes `ai-report.css` and updates the embedded UI report.

---

## 🤖 How AI Analysis Works

After pytest executes the tests, all failure metadata is passed to Claude via the CLI:

* Error message
* Stack trace
* Test title + node ID
* stdout/stderr logs
* Original user story (for context)

Claude returns structured HTML with:

### **1. Plain-English Explanation**

Why did this fail?

### **2. Probable Root Causes**

2–3 likely technical problems.

### **3. Suggested Test Fixes**

Specific pytest-playwright code improvements.

### **4. Flakiness Mitigation**

Ways to reduce intermittent failures.

---

## 🎨 HTML Dashboard Themes & Features

* Dark-mode
* Animated gradient highlight bars
* Glowing hover transitions
* Status badges
* Collapsible AI analysis sections
* External CSS for easy editing
* Radial gradients & neon accent hues

---

## 🧪 Example AI Output (HTML)

```
<h3>Plain-English Explanation</h3>
<p>The success message never appeared...</p>

<h3>Probable Root Causes</h3>
<ul>
  <li>Selector mismatch</li>
  <li>API response delay</li>
  <li>Redirect timing issue</li>
</ul>

<h3>Suggested Test Fixes</h3>
<ul>
  <li>Use page.wait_for_url('/dashboard')</li>
  <li>Wait for stable locator instead of get_by_text</li>
</ul>

<h3>Flakiness Mitigation</h3>
<p>Increase timeout or add a network idle wait.</p>
```

---

## 📦 Environment Variables

**No API keys required!** The project uses the **Claude Code CLI**, which authenticates with your Claude Code subscription.

If you want to specify a particular Claude model (optional), use:
```bash
claude --model claude-opus-4-7
```

This sets the model for all subsequent `claude -p` commands during the pipeline run.

---

## 🧭 Roadmap & Enhancements

* Multi-story batch generation
* Test-to-story reverse engineering
* Hit-map UI of frequent failures
* CI pipeline integration
* Slack/Teams bot that posts AI insights
* Flaky test scoring over time

---

## 💬 Contributing

Pull requests welcome!

Open issues for bugs, ideas, or UX/UI enhancements.

---

## ⭐ Star the repo if you like it!

This project helps show how AI can supercharge real-world QA automation.

Let's build the future of testing. 🔥
