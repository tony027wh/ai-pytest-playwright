import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils.opencode_client import opencode_prompt as claude_prompt
from utils.test_helpers import config_base_url, extract_base_url, extract_story_type, strip_markdown_fences

SYSTEM_MSG_UI = (
    "你是一个 pytest-playwright 测试代码生成器。"
    "只输出完整的 Python 代码作为 pytest 测试。"
    "不要包含任何解释、关于代码的注释或 markdown 格式。"
    '直接以 "from playwright.sync_api import Page, expect" 开头。'
)

USER_MSG_TEMPLATE_UI = """根据以下用户故事生成一个 Python 的 pytest-playwright 测试（单个测试）：

{story}

要求：
- 以: from playwright.sync_api import Page, expect 开头
- 使用 pytest 夹具: def test_{slug}(page: Page):
- 该仓库的基础 URL 为: {base_url}
  用它来构造任何相对路径的完整 URL（例如 /login → {base_url}/login）。
  如果故事明确指向另一个站点，则改用该站点的 URL。
- 使用 page.goto()、page.locator()、page.fill()、page.click()、expect(...)
- 使用验收标准中的数据。
- expect(page).to_have_url() 和 expect(page).to_have_title() 各自只接受一个字符串（精确匹配）或 re.Pattern（部分/正则匹配）。绝不能向它们传递 lambda 或可调用对象——否则会引发 TypeError。对于部分/包含检查，使用 re.compile()，例如 expect(page).to_have_url(re.compile(r"/status_codes/200")) 或 expect(page).to_have_title(re.compile(r"Wikipedia"))。使用 re.compile() 时，请在 playwright 导入之后添加 "import re"。
- 当标准中提到"页面加载成功"但没有指定 URL 时，断言页面标题或一个关键可见元素——绝不要自行发明 URL 断言。例如: expect(page).to_have_title(re.compile(r"关键词", re.IGNORECASE)) 或 expect(page.locator("h1")).to_be_visible()。
- 只输出 Python 代码。不要解释，不要 markdown，不要注释。
- 直接以 "from playwright.sync_api import Page, expect" 开头。"""

SYSTEM_MSG_API = (
    "你是一个使用 httpx 进行 REST API 测试的 pytest 测试代码生成器。"
    "只输出完整的 Python 代码作为 pytest 测试。"
    "不要包含任何解释、关于代码的注释或 markdown 格式。"
    '直接以 "import httpx" 开头。'
)

USER_MSG_TEMPLATE_API = """根据以下用户故事生成一个使用 httpx 的 pytest 测试（单个测试）：

{story}

要求：
- 以: import httpx 开头
- 使用 pytest 函数: def test_{slug}():  （没有 page 夹具——这是一个 API 测试）
- 基础 URL 为: {base_url}
  用它来构造任何相对路径的完整 URL（例如 /users/1 → {base_url}/users/1）。
  如果故事明确指向另一个主机，则改用该主机。
- 使用 httpx.get()、httpx.post()、httpx.put()、httpx.patch()、httpx.delete() 进行 HTTP 调用。
- 断言 response.status_code 等于期望值。
- 使用 response.json() 解析 JSON，并使用普通 Python 断言检查各个字段。
- 当故事需要时，通过 response.headers 断言响应头。
- 对于故事中写作 {{VARIABLE_NAME}} 的密钥/令牌，使用 os.environ.get("VARIABLE_NAME") 读取它们，并在顶部添加 "import os"。
- 编写清晰的 AssertionError 消息，例如 assert body["id"] == 1, f"期望 id=1，得到 {{body['id']}}"
- 只输出 Python 代码。不要解释，不要 markdown，不要注释。
- 直接以 "import httpx" 开头。"""


def generate_for_story(story_path: Path) -> None:
    """根据故事文件生成测试代码并写入 tests/ 目录。"""
    story = story_path.read_text(encoding="utf-8")
    slug = story_path.stem

    # 故事级别的基础 URL 优先；否则回退到仓库配置。
    base_url = extract_base_url(story) or config_base_url()

    story_type = extract_story_type(story)
    if story_type == "api":
        system_msg = SYSTEM_MSG_API
        user_msg = USER_MSG_TEMPLATE_API.format(story=story, slug=slug, base_url=base_url)
    else:
        system_msg = SYSTEM_MSG_UI
        user_msg = USER_MSG_TEMPLATE_UI.format(story=story, slug=slug, base_url=base_url)

    out_path = Path("tests") / f"test_{slug}.py"

    code = claude_prompt(system_msg, user_msg)

    code = strip_markdown_fences(code)

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f"为 {slug} 生成的代码存在语法错误: {e}", file=sys.stderr)
        sys.exit(1)

    expected_fn = f"test_{slug}"
    fn_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    if expected_fn not in fn_names:
        print(
            f"为 {slug} 生成的代码缺少函数 '{expected_fn}'（找到: {fn_names}）",
            file=sys.stderr,
        )
        sys.exit(1)

    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(code, encoding="utf-8")
    print(f"已生成: {out_path}")


def main() -> None:
    """从故事文件生成 pytest 测试的主入口点。"""
    parser = argparse.ArgumentParser(description="从故事文件生成 pytest 测试")
    parser.add_argument("--story", help="特定的故事文件名（例如 login.md）")
    args = parser.parse_args()

    stories_dir = Path("stories")
    if not stories_dir.exists():
        print("未找到 stories/ 目录。", file=sys.stderr)
        sys.exit(1)

    if args.story:
        story_path = stories_dir / args.story
        if not story_path.exists():
            print(f"未找到故事文件: {args.story}", file=sys.stderr)
            sys.exit(1)
        generate_for_story(story_path)
        return

    files = sorted(stories_dir.glob("*.md"))
    if not files:
        print("在 ./stories 中未找到 .md 故事文件", file=sys.stderr)
        sys.exit(1)

    for story_path in files:
        generate_for_story(story_path)


if __name__ == "__main__":
    main()
