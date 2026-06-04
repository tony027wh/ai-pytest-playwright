import argparse
import ast
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
- expect(page).to_have_url() and expect(page).to_have_title() each accept only a string (exact match) or re.Pattern (partial/regex match). NEVER pass a lambda or callable to either — it will raise a TypeError. For partial/contains checks use re.compile(), e.g. expect(page).to_have_url(re.compile(r"/status_codes/200")) or expect(page).to_have_title(re.compile(r"Wikipedia")). Add "import re" after the playwright import when using re.compile().
- When a criterion says "the page loads successfully" without specifying a URL, assert the page title or a key visible element — never invent a URL assertion. Example: expect(page).to_have_title(re.compile(r"keyword", re.IGNORECASE)) or expect(page.locator("h1")).to_be_visible().
- Output ONLY the Python code. No explanations, no markdown, no comments.
- Start directly with "from playwright.sync_api import Page, expect"."""


def _config_base_url() -> str:
    """Read the default base_url from test_config.yaml, falling back to empty string."""
    try:
        from shared_utils.core.config_loader import load_config
        cfg = load_config("test_config.yaml")
        adapter_env = cfg["app"]["default_env"]
        return cfg["environments"].get(adapter_env, {}).get("base_url", "")
    except Exception as e:
        print(f"Warning: could not read base_url from test_config.yaml: {e}", file=sys.stderr)
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

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"Generated code for {slug} has a syntax error: {e}", file=sys.stderr)
        sys.exit(1)

    expected_fn = f"test_{slug}"
    fn_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if expected_fn not in fn_names:
        print(
            f"Generated code for {slug} is missing function '{expected_fn}' (found: {fn_names})",
            file=sys.stderr,
        )
        sys.exit(1)

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
