import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils.claude_client import claude_prompt

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
- Use the Base URL from the story. If present, prepend it to any relative paths like /login.
- Use page.goto(), page.locator(), page.fill(), page.click(), expect(...)
- Use data from the Acceptance criteria.
- Output ONLY the Python code. No explanations, no markdown, no comments.
- Start directly with "from playwright.sync_api import Page, expect"."""


def generate_for_story(story_path: Path) -> None:
    story = story_path.read_text(encoding="utf-8")
    slug = story_path.stem

    out_path = Path("tests") / f"test_{slug}.py"

    user_msg = USER_MSG_TEMPLATE.format(story=story, slug=slug)
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
