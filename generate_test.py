import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils.claude_client import claude_prompt
from utils.test_helpers import extract_base_url

SYSTEM_MSG = (
    "You are a pytest-playwright test code generator. "
    "Output ONLY the complete Python code for a pytest test. "
    "Do not include any explanations, comments about the code, or markdown formatting. "
    'Start directly with "from playwright.sync_api import Page, expect".'
)

USER_MSG_TEMPLATE = """Generate a SINGLE pytest-playwright test in Python based on this user story:

{story}

Requirements:
- Start with: from playwright.sync_api import Page, expect
- Use pytest fixture: def test_{slug}(page: Page):
- Base URL for this repo is: {base_url}
  Use it to construct full URLs for any relative paths (e.g. /login → {base_url}/login).
  If the story clearly targets a different site, use that site's URL instead.
- Use page.goto(), page.locator(), page.fill(), page.click(), expect(...)
- Use data from the Acceptance criteria.
- For URL assertions: expect(page).to_have_url() accepts only a string (exact match) or re.Pattern (partial/regex match). NEVER pass a lambda or callable. For partial URL checks use re.compile(), e.g. expect(page).to_have_url(re.compile(r"/status_codes/200")) and add "import re" after the playwright import.
- Output ONLY the Python code. No explanations, no markdown, no comments.
- Start directly with "from playwright.sync_api import Page, expect"."""


def _config_base_url() -> str:
    """Read the default base_url from test_config.yaml, falling back to empty string."""
    try:
        from shared_utils.core.config_loader import load_config
        cfg = load_config("test_config.yaml")
        adapter_env = cfg["app"]["default_env"]
        # _resolve_env is on the adapter; replicate the simple case here
        import os, re as _re
        m = _re.match(r"^\$\{(\w+)(?::-(.*))?\}$", adapter_env)
        if m:
            adapter_env = os.environ.get(m.group(1), m.group(2) or "")
        return cfg["environments"].get(adapter_env, {}).get("base_url", "")
    except Exception:
        return ""


def generate_for_story(story_path: Path) -> None:
    story = story_path.read_text(encoding="utf-8")
    slug = story_path.stem

    # Story-level Base URL takes priority; fall back to repo config.
    base_url = extract_base_url(story) or _config_base_url()

    out_path = Path("tests") / f"test_{slug}.py"

    user_msg = USER_MSG_TEMPLATE.format(story=story, slug=slug, base_url=base_url)
    code = claude_prompt(SYSTEM_MSG, user_msg)

    code = re.sub(r"```[a-zA-Z]*", "", code).replace("```", "").strip()

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(code, encoding="utf-8")
    print(f"Generated: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate pytest tests from story files")
    parser.add_argument("--story", help="Specific story filename (e.g. login.md)")
    args = parser.parse_args()

    stories_dir = Path("stories")
    if not stories_dir.exists():
        print("No stories/ directory found.", file=sys.stderr)
        sys.exit(1)

    if args.story:
        story_path = stories_dir / args.story
        if not story_path.exists():
            print(f"Story not found: {args.story}", file=sys.stderr)
            sys.exit(1)
        generate_for_story(story_path)
        return

    files = sorted(stories_dir.glob("*.md"))
    if not files:
        print("No .md story files found in ./stories", file=sys.stderr)
        sys.exit(1)

    for story_path in files:
        generate_for_story(story_path)


if __name__ == "__main__":
    main()
