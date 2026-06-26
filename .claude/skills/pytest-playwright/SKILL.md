# pytest-playwright 技能

你是本项目的 pytest-playwright 专家。当用户要求你编写、运行、修复或探索 Playwright 测试时，请使用本指南。

## 项目数据流

```
stories/*.md
  → python generate_test.py [--story <file>]
      → tests/test_*.py
          → python -m pytest [tests/test_<slug>.py] [-v --json-report --json-report-file=pytest-report.json]
              → python analyze/analyze_failures.py [--html]
                  → ai-analysis.json  +  ai-report.html
```

完整流水线快捷方式：
```bash
python pipeline.py [--story login.md] [--test test_login.py]
```

## 故事格式

故事文件位于 `stories/<slug>.md`。slug 成为测试函数名。

```markdown
Title: <描述性标题>

Base URL: https://example.com   ← 如果应用已在 test_config.yaml 中配置，则为可选

As a user, I want to <目标>.

Acceptance criteria:
- Navigate to `/path`
- Fill in <字段> `value`
- Click the <按钮>
- Expect <断言>
```

`Base URL:` 是可选的。如果省略，`generate_test.py` 从 `test_config.yaml` 读取默认值
（`environments.<default_env>.base_url`）。仅当故事针对与仓库默认值**不同**的站点时才包含 `Base URL:`。
验收标准中使用相对路径（`/login`）——生成器会自动添加 base URL 前缀。

## 测试文件格式

测试位于 `tests/test_<slug>.py`。每个文件一个测试函数，以 slug 命名。

```python
from playwright.sync_api import Page, expect


def test_<slug>(page: Page):
    page.goto("https://example.com/path")
    page.get_by_label("Username").fill("tomsmith")
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_url("https://example.com/secure")
    expect(page.get_by_role("alert")).to_contain_text("You logged into a secure area!")
```

规则：
- 始终以 `from playwright.sync_api import Page, expect` 开头
- 使用 pytest 的 `page: Page` 夹具——绝不在测试文件中实例化 `sync_playwright()`
- `base_url` 在 `browser_context_args` 中从 `test_config.yaml` 设置——你可以使用相对路径如 `page.goto("/login")`，或完整 URL，两者都有效
- 一个 `def test_<slug>(page: Page):` 函数，不使用类包装（除非使用 POM——见下文）

## 命令参考

```bash
# 从故事文件生成测试
python generate_test.py                    # 所有故事
python generate_test.py --story login.md   # 单个故事

# 运行测试
python -m pytest                           # 所有测试
python -m pytest tests/test_login.py -v    # 单个测试，详细输出
python -m pytest --json-report --json-report-file=pytest-report.json  # 输出 JSON 格式

# 分析失败（需要 pytest-report.json）
python analyze/analyze_failures.py         # 仅 JSON 输出
python analyze/analyze_failures.py --html  # JSON + HTML 报告（自动打开浏览器）

# 完整流水线
python pipeline.py
python pipeline.py --story login.md --test test_login.py

# UI 服务器
uvicorn server.server:app --port 5173
```

所有命令从项目根目录运行。虚拟环境位于 `.venv/`。

## 临时探索

当你需要快速测试定位器或探索页面而不添加永久测试时，编写一个临时脚本到 `/tmp/` 并直接运行——不要将其放在 `tests/` 中：

```python
# /tmp/pw_scratch.py
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    page = browser.new_page()
    page.goto("https://the-internet.herokuapp.com/login")
    print(page.title())
    # 检查、截图等
    browser.close()
```

```bash
python /tmp/pw_scratch.py
```

清理：`rm /tmp/pw_scratch.py`

探索时使用 `headless=False` 和 `slow_mo=100`，以便你能看到正在发生的事情。

## 页面对象模型（POM）

本项目目前未使用 POM。仅当某个页面在多个测试文件之间共享时才引入 POM。结构如下：

```
pages/
  login_page.py      # LoginPage 类
tests/
  test_login.py      # 导入 LoginPage
  test_secure.py     # 导入 LoginPage
```

页面对象模式：
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

断言保留在测试文件中，不要放在页面对象中。

## 定位器策略

按以下优先级选择：
1. `get_by_role("button", name="Submit")` — 语义化、可访问
2. `get_by_label("Username")` — 用于带标签的输入框
3. `get_by_text("Welcome")` — 用于可见文本
4. `get_by_placeholder("Enter email")` — 用于通过占位符定位输入框
5. `locator("#id")` 或 `locator("[data-testid=foo]")` — 仅在语义化定位器不可用时使用
6. 绝不使用脆弱的 CSS，如 `nth-child`、位置型 XPath 或长后代选择器

## URL 和标题断言

`expect(page).to_have_url()` 和 `expect(page).to_have_title()` 各自只接受 `str`（精确匹配）或 `re.Pattern`（部分/正则匹配）。绝不要传递 lambda 或可调用对象——会引发 `TypeError`。

当验收标准中说 **"包含"**（例如"页面标题包含 'Wikipedia'"）时，应转换为 `re.compile()`——绝不使用 lambda：

```python
import re

expect(page).to_have_url(re.compile(r"/status_codes/200"))
expect(page).to_have_title(re.compile(r"Wikipedia"))
```

## "页面加载成功"

当故事标准中说"页面加载成功"而未指定 URL 时，断言页面标题或关键可见元素——绝不要编造 URL 断言：

```python
expect(page).to_have_title(re.compile(r"HDMI", re.IGNORECASE))  # 标题证明页面已加载
expect(page.locator("h1")).to_be_visible()                       # 或关键元素
```

URL 断言确认的是导航，而非页面加载。仅当故事明确说明 URL 应为何值时，才添加 `to_have_url()`。

## 等待策略

绝不要使用 `page.wait_for_timeout()`（硬编码休眠）。使用：

```python
page.wait_for_url("**/secure")          # 导航后
page.wait_for_load_state("networkidle") # 页面加载量大时
expect(locator).to_be_visible()         # 自动等待，最长默认超时时间
expect(locator).to_contain_text("...")  # 自动等待
```

Playwright 的 `expect()` 断言默认自动重试最多 5 秒——依赖它们。

## 文件命名约定

| 故事文件 | 测试文件 | 测试函数 |
|---|---|---|
| `stories/login.md` | `tests/test_login.py` | `def test_login(page: Page):` |
| `stories/add_remove_elements.md` | `tests/test_add_remove_elements.py` | `def test_add_remove_elements(page: Page):` |

slug 始终是故事文件名的主干，使用蛇形命名法。

## 新测试工作流程

1. 编写 `stories/<slug>.md`，包含标题、Base URL 和验收标准
2. 运行 `python generate_test.py --story <slug>.md` 生成测试
3. 检查 `tests/test_<slug>.py` — 如有需要，编辑定位器或断言
4. 运行 `python -m pytest tests/test_<slug>.py -v` 验证
5. 如果失败，运行 `python analyze/analyze_failures.py --html` 进行 AI 诊断
