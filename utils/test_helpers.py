import re
import sys
from pathlib import Path
from typing import Optional


def config_base_url() -> str:
    try:
        from shared_utils.core.config_loader import load_config
        cfg = load_config("test_config.yaml")
        adapter_env = cfg["app"]["default_env"]
        return cfg["environments"].get(adapter_env, {}).get("base_url", "")
    except Exception as e:
        print(f"Warning: could not read base_url from test_config.yaml: {e}", file=sys.stderr)
        return ""


def strip_markdown_fences(code: str) -> str:
    code = re.sub(r"```[a-zA-Z]*", "", code)
    code = code.replace("```", "")
    return code.strip()


def extract_base_url(story_content: str) -> Optional[str]:
    match = re.search(r"Base URL:\s*(https?://\S+)", story_content, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_story_title(story_content: str) -> Optional[str]:
    match = re.search(r"Title:\s*(.+)", story_content, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_acceptance_criteria(story_content: str) -> list:
    lines = story_content.split("\n")
    criteria = []
    in_criteria = False

    for line in lines:
        if re.search(r"acceptance(?:\s+criteria)?|^ac\s*:", line, re.IGNORECASE):
            in_criteria = True
            continue
        if in_criteria:
            if line.strip().startswith("-"):
                criteria.append(line.strip())
            elif line.strip() and not re.match(r"^[A-Z]", line.strip()):
                criteria.append(line.strip())
            elif line.strip() and re.match(r"^[A-Z]", line.strip()) and not line.strip().startswith("-"):
                break

    return criteria


def collect_failed_tests(tests: list) -> list:
    failed = []
    for test in tests:
        if test.get("outcome") == "failed":
            call = test.get("call") or {}
            crash = call.get("crash") or {}
            failed.append({
                "nodeid": test.get("nodeid", ""),
                "outcome": test.get("outcome", ""),
                "longrepr": call.get("longrepr", ""),
                "crash_message": crash.get("message", ""),
            })
    return failed


def nodeid_to_slug(nodeid: str) -> str:
    parts = nodeid.split("::")
    if not parts:
        return ""
    stem = Path(parts[0]).stem  # e.g. "test_login"
    return stem[5:] if stem.startswith("test_") else stem


def validate_story_text(text: str) -> dict:
    errors = []
    warnings = []

    t = (text or "").strip()
    if not t:
        errors.append("Story text is empty.")

    has_acceptance = bool(re.search(
        r"(?:^|\n)\s*(acceptance(?:\s+criteria)?|ac)\s*:?\s*",
        t, re.IGNORECASE
    ))
    has_bullets = bool(re.search(r"(^|\n)\s*-\s+.+", t, re.MULTILINE))

    if not has_acceptance:
        warnings.append("Missing an 'Acceptance:' section (recommended).")
    if not has_bullets:
        warnings.append("No bullet steps found (e.g. '- Navigate to ...').")

    has_url = bool(re.search(r"https?://\S+", t, re.IGNORECASE))
    if not has_url:
        warnings.append("No Base URL in story — repo default from test_config.yaml will be used.")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}
