import asyncio
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.claude_client import claude_prompt
from utils.test_helpers import validate_story_text

PROJECT_ROOT = Path(__file__).parent.parent
UI_DIR = PROJECT_ROOT / "ui"
STORIES_DIR = PROJECT_ROOT / "stories"
TESTS_DIR = PROJECT_ROOT / "tests"
PORT = int(os.environ.get("PORT", 5173))

app = FastAPI()
_run_lock = asyncio.Lock()


# ─── Validators ───────────────────────────────────────────────────────────────

def safe_file_name(input_str: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", str(input_str).strip().lower())
    result = result.strip("_")[:80]
    return result or "story"


def safe_story_file(input_str: str) -> Optional[str]:
    raw = str(input_str or "").strip()
    if not raw or "/" in raw or "\\" in raw or ".." in raw:
        return None
    if not raw.endswith(".md"):
        return None
    return raw


def safe_test_file(input_str: str) -> Optional[str]:
    raw = str(input_str or "").strip()
    if not raw or "/" in raw or "\\" in raw or ".." in raw:
        return None
    if not raw.endswith(".py") or not raw.startswith("test_"):
        return None
    return raw


def next_untitled_story_name() -> str:
    files = [f.name for f in STORIES_DIR.glob("untitled_story_*.md")]
    max_num = 0
    for f in files:
        m = re.match(r"^untitled_story_(\d+)\.md$", f)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"untitled_story_{max_num + 1}"


def is_duplicate_story(content: str) -> Optional[str]:
    normalized = (content or "").strip()
    if not normalized:
        return None
    for f in STORIES_DIR.glob("*.md"):
        if f.read_text(encoding="utf-8").strip() == normalized:
            return f.name
    return None


# ─── Run helper ───────────────────────────────────────────────────────────────

async def run_command(command: str) -> dict:
    if _run_lock.locked():
        return {"ok": False, "error": "Pipeline already running.", "_locked": True}

    async with _run_lock:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "exitCode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }


# ─── API routes ───────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/stories")
async def list_stories():
    STORIES_DIR.mkdir(exist_ok=True)
    files = sorted(f.name for f in STORIES_DIR.glob("*.md"))
    return {"files": files}


@app.post("/api/stories")
async def save_story(request: Request):
    body = await request.json()
    content = (body.get("content") or "").strip()
    filename = str(body.get("filename") or "").strip()

    v = validate_story_text(content)
    if not v["ok"]:
        return JSONResponse(status_code=400, content=v)

    duplicate = is_duplicate_story(content)
    if duplicate:
        return JSONResponse(
            status_code=409,
            content={"ok": False, "error": f"Duplicate story content matches {duplicate}."},
        )

    STORIES_DIR.mkdir(exist_ok=True)
    base = safe_file_name(filename) if filename else next_untitled_story_name()
    out_path = STORIES_DIR / f"{base}.md"
    out_path.write_text(content, encoding="utf-8")
    return {"ok": True, "savedAs": f"{base}.md", **v}


@app.delete("/api/stories")
async def delete_all_stories():
    files = list(STORIES_DIR.glob("*.md"))
    for f in files:
        f.unlink()
    return {"ok": True, "deletedCount": len(files)}


@app.get("/api/story")
async def get_story(name: str = Query(...)):
    safe = safe_story_file(name)
    if not safe:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid story name."})
    path = STORIES_DIR / safe
    if not path.exists():
        return JSONResponse(status_code=404, content={"ok": False, "error": "Not found."})
    return {"ok": True, "name": safe, "content": path.read_text(encoding="utf-8")}


@app.delete("/api/story")
async def delete_story(name: str = Query(...)):
    safe = safe_story_file(name)
    if not safe:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid story name."})
    path = STORIES_DIR / safe
    if not path.exists():
        return JSONResponse(status_code=404, content={"ok": False, "error": "Not found."})
    path.unlink()
    return {"ok": True, "deleted": safe}


@app.get("/api/tests")
async def list_tests():
    TESTS_DIR.mkdir(exist_ok=True)
    files = sorted(
        f.name for f in TESTS_DIR.glob("test_*.py")
        if f.is_file()
    )
    return {"files": files}


@app.delete("/api/tests")
async def delete_all_tests():
    files = [f for f in TESTS_DIR.glob("test_*.py") if f.is_file()]
    for f in files:
        f.unlink()
    return {"ok": True, "deletedCount": len(files)}


@app.get("/api/test")
async def get_test(name: str = Query(...)):
    safe = safe_test_file(name)
    if not safe:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid test name."})
    path = TESTS_DIR / safe
    if not path.exists():
        return JSONResponse(status_code=404, content={"ok": False, "error": "Not found."})
    return {"ok": True, "name": safe, "content": path.read_text(encoding="utf-8")}


@app.put("/api/test")
async def update_test(name: str = Query(...), request: Request = None):
    safe = safe_test_file(name)
    if not safe:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid test name."})
    body = await request.json()
    content = str(body.get("content") or "")
    if not content.strip():
        return JSONResponse(status_code=400, content={"ok": False, "error": "Test content is empty."})
    path = TESTS_DIR / safe
    path.write_text(content, encoding="utf-8")
    return {"ok": True, "saved": safe}


@app.delete("/api/test")
async def delete_test(name: str = Query(...)):
    safe = safe_test_file(name)
    if not safe:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid test name."})
    path = TESTS_DIR / safe
    if not path.exists():
        return JSONResponse(status_code=404, content={"ok": False, "error": "Not found."})
    path.unlink()
    return {"ok": True, "deleted": safe}


@app.post("/api/validate")
async def validate_story(request: Request):
    body = await request.json()
    return validate_story_text(body.get("content") or "")


@app.post("/api/run/ai-gen")
async def run_ai_gen(story: Optional[str] = Query(None)):
    safe = safe_story_file(story) if story else None
    if safe:
        cmd = f'python generate_test.py --story "{safe}"'
    else:
        cmd = "python generate_test.py"
    result = await run_command(cmd)
    if result.get("_locked"):
        return JSONResponse(status_code=429, content={"ok": False, "error": result["error"]})
    return result


@app.post("/api/run/tests")
async def run_tests(test: Optional[str] = Query(None)):
    safe = safe_test_file(test) if test else None
    if safe:
        cmd = f"python -m pytest tests/{safe}"
    else:
        cmd = "python -m pytest"
    result = await run_command(cmd)
    if result.get("_locked"):
        return JSONResponse(status_code=429, content={"ok": False, "error": result["error"]})
    return result


@app.post("/api/run/analyze")
async def run_analyze(html: Optional[str] = Query(None), report: Optional[str] = Query(None)):
    wants_html = html != "0" and report != "0"
    cmd = "python analyze/analyze_failures.py --html" if wants_html else "python analyze/analyze_failures.py"
    result = await run_command(cmd)
    if result.get("_locked"):
        return JSONResponse(status_code=429, content={"ok": False, "error": result["error"]})
    return result


@app.post("/api/run/report")
async def run_report():
    result = await run_command("python analyze/analyze_failures.py --html")
    if result.get("_locked"):
        return JSONResponse(status_code=429, content={"ok": False, "error": result["error"]})
    return result


@app.post("/api/run/pipeline")
async def run_pipeline():
    result = await run_command("python pipeline.py")
    if result.get("_locked"):
        return JSONResponse(status_code=429, content={"ok": False, "error": result["error"]})
    return result


@app.post("/api/ai/story")
async def ai_story(request: Request):
    body = await request.json()
    requirements = body.get("requirements") or ""
    selectors = body.get("selectors") or "n/a"
    user_path = body.get("path") or "n/a"
    expected = body.get("expected") or ""

    if not requirements or not expected:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Requirements and expected outcome are required."},
        )

    prompt = f"""You are a QA analyst writing user stories for test automation.

Create a concise story in plain English. Format:

Title: <short title>
Base URL: <optional if provided>
Story:
As a user, I want to ...

Acceptance:
- ...
- ...
- ...

Inputs:
Requirements: {requirements}
Selectors/UI: {selectors}
Path/Steps: {user_path}
Expected outcome: {expected}""".strip()

    try:
        story_text = claude_prompt("You write crisp user stories for QA. No markdown.", prompt)
        return {"ok": True, "story": story_text}
    except Exception:
        return JSONResponse(status_code=500, content={"ok": False, "error": "AI generation failed."})


@app.post("/api/ai/fix-test")
async def ai_fix_test(request: Request):
    body = await request.json()
    test_title = str(body.get("testTitle") or "")
    test_file = str(body.get("testFile") or "")
    stdout = str(body.get("stdout") or "")
    stderr = str(body.get("stderr") or "")
    error_context_paths = body.get("errorContextPaths") or []

    safe = safe_test_file(test_file)

    # If testFile not directly usable, try to derive from testTitle (nodeid format)
    if not safe and test_title:
        # testTitle may be a nodeid like "tests/test_login.py::test_login"
        # or just "test_login.py"
        m = re.search(r"(test_[^:/\s]+\.py)", test_title)
        if m:
            safe = safe_test_file(m.group(1))

    # Last resort: search test files for matching function name
    if not safe and test_title:
        func_match = re.search(r"::(\w+)$", test_title)
        func_name = func_match.group(1) if func_match else None
        if func_name:
            for f in TESTS_DIR.glob("test_*.py"):
                if f.is_file() and func_name in f.read_text(encoding="utf-8"):
                    safe = safe_test_file(f.name)
                    if safe:
                        break

    if not safe:
        return JSONResponse(status_code=400, content={"ok": False, "error": "Invalid test file."})

    test_path = TESTS_DIR / safe
    if not test_path.exists():
        return JSONResponse(status_code=404, content={"ok": False, "error": "Test file not found."})

    current_test = test_path.read_text(encoding="utf-8")

    # Load story context
    story_context = ""
    try:
        slug = re.sub(r"^test_", "", Path(safe).stem)
        story_path = STORIES_DIR / f"{slug}.md"
        if story_path.exists():
            story_context = story_path.read_text(encoding="utf-8")
    except Exception:
        pass

    prompt = f"""You are a senior QA engineer specializing in Playwright.
You will receive a failing test and logs. Return the FULL corrected test file contents only.
Do not include markdown fences or commentary.

Test title: {test_title}
Test file: {safe}

Current test file:
{current_test}

Run stdout:
{stdout}

Run stderr:
{stderr}

Related story (if any):
{story_context}

Requirements:
- Preserve the file structure and imports if possible.
- Fix the test based on the real behavior of https://the-internet.herokuapp.com when applicable.
- Return ONLY the corrected file contents.""".strip()

    try:
        fixed_content = claude_prompt("You fix pytest-playwright tests. Return full file contents only.", prompt)
        if not fixed_content:
            return JSONResponse(status_code=500, content={"ok": False, "error": "AI returned empty response."})

        # Generate summary
        summary = ""
        try:
            summary_prompt = f"""Summarize the fix in 1-2 sentences, focusing on what changed and why.

Original test:
{current_test[:4000]}

Updated test:
{fixed_content[:4000]}""".strip()
            summary = claude_prompt("Summarize test fixes concisely.", summary_prompt)
        except Exception:
            pass

        # Backup and write
        backup_dir = TESTS_DIR / ".ai-backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"{safe}.{int(time.time() * 1000)}.bak"
        backup_path.write_text(current_test, encoding="utf-8")
        test_path.write_text(fixed_content + "\n", encoding="utf-8")

        return {
            "ok": True,
            "updatedFile": safe,
            "preview": fixed_content[:2000],
            "summary": summary,
        }
    except Exception:
        return JSONResponse(status_code=500, content={"ok": False, "error": "AI fix failed."})


# ─── Static file serving ──────────────────────────────────────────────────────

@app.get("/ai-report.html")
async def serve_ai_report():
    path = PROJECT_ROOT / "ai-report.html"
    if not path.exists():
        return Response(status_code=404)
    return FileResponse(path, media_type="text/html")


@app.get("/ai-report.css")
async def serve_ai_report_css():
    path = PROJECT_ROOT / "ai-report.css"
    if not path.exists():
        return Response(status_code=404)
    return FileResponse(path, media_type="text/css")


@app.get("/ai-analysis.json")
async def serve_ai_analysis():
    path = PROJECT_ROOT / "ai-analysis.json"
    if not path.exists():
        return Response(status_code=404)
    return FileResponse(path, media_type="application/json")


@app.get("/playwright-report/{path:path}")
async def serve_playwright_report(path: str):
    report_root = PROJECT_ROOT / "playwright-report"
    if not path or path == "/":
        file_path = report_root / "index.html"
    else:
        file_path = report_root / path
    # Prevent path traversal
    try:
        file_path.resolve().relative_to(report_root.resolve())
    except ValueError:
        return Response(status_code=403)
    if not file_path.exists():
        return Response(status_code=404)
    if file_path.is_dir():
        file_path = file_path / "index.html"
        if not file_path.exists():
            return Response(status_code=404)
    return FileResponse(file_path)


# Mount UI static files last (catch-all)
if UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.server:app", host="0.0.0.0", port=PORT, reload=False)
