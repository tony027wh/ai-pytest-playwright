# AI Pytest-Playwright

一个端到端的 AI 驱动测试自动化流水线，将纯英文的用户故事转化为可运行的 Playwright 测试，用 OpenCode 分析失败原因，并生成样式化的 HTML 报告。

---

## 目录

- [AI Pytest-Playwright](#ai-pytest-playwright)
  - [目录](#目录)
  - [技术栈](#技术栈)
  - [项目结构](#项目结构)
  - [安装](#安装)
  - [工作流程：运行所有测试](#工作流程运行所有测试)
  - [工作流程：添加新故事并测试](#工作流程添加新故事并测试)
  - [独立命令参考](#独立命令参考)
  - [UI 仪表盘](#ui-仪表盘)
  - [OpenCode 技能](#opencode-技能)
  - [AI 分析工作原理](#ai-分析工作原理)
  - [跨仓库工具设计](#跨仓库工具设计)
    - [工作原理](#工作原理)
    - [将其添加到另一个仓库](#将其添加到另一个仓库)
    - [共享工具集](#共享工具集)
  - [路线图](#路线图)

---

## 技术栈

- **Python 3.13+**
- **pytest + pytest-playwright**
- **OpenCode CLI** — 无需 API 密钥，使用你的 OpenCode 订阅
- **FastAPI** 用于本地 UI 服务器
- **深色模式 HTML 仪表盘**，使用外部 CSS

---

## 项目结构

```
ai-pytest-playwright/
│
├── stories/                       # 纯英文测试规格说明 (.md)
├── tests/                         # 自动生成的 pytest-playwright 测试
│   └── .ai-backups/               # AI 修复前创建的备份
│
├── shared_utils/                  # 可复用的工具库（可复制到任何仓库）
│   ├── adapters/
│   │   └── base.py                # AppAdapter 抽象基类 — 每个仓库行为的抽象接口
│   └── core/
│       ├── config_loader.py       # 加载 test_config.yaml，解析 ${ENV_VAR:-default}
│       ├── retry.py               # retry() 和 wait_for() 辅助函数
│       └── assertions.py         # SoftAssertions — 收集失败信息，最后统一抛出
│
├── adapters/
│   └── the_internet_adapter.py   # 本仓库目标应用的具体 AppAdapter 实现
│
├── analyze/
│   └── analyze_failures.py       # AI 失败分析引擎
├── utils/
│   ├── opencode_client.py          # OpenCode CLI 子进程辅助函数
│   └── test_helpers.py           # 共享测试工具
├── server/
│   └── server.py                 # FastAPI 服务器
├── ui/                           # 前端（index.html, ui.js, ui.css, modules/）
│
├── test_config.yaml              # 仓库级配置：环境、浏览器、认证、路由
├── generate_test.py              # 将故事转换为 pytest 测试
├── pipeline.py                   # 完整流水线编排器
├── conftest.py                   # pytest + Playwright 夹具（配置驱动）
├── pytest.ini                    # pytest 配置
└── requirements.txt
```

**数据流：**
```
test_config.yaml  ←─ conftest.py  ←─ adapters/the_internet_adapter.py
                                         │
stories/*.md                             │ base_url、浏览器设置、认证
  → generate_test.py                     │
      → tests/test_*.py ───────────────→ pytest  →  pytest-report.json  +  playwright-report/
                                              → analyze_failures.py
                                                  → ai-analysis.json  +  ai-report.html
```

---

## 安装

```bash
git clone https://github.com/andrewtdinh/ai-pytest-playwright.git
cd ai-pytest-playwright
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install
```

无需 API 密钥。该项目使用 **OpenCode CLI**（`opencode` 命令），该命令包含在你的 OpenCode 订阅中。如果尚未安装，请[在此获取 OpenCode](https://claude.ai/code)。

---

## 工作流程：运行所有测试

当你想要端到端运行整个测试套件时使用。

**步骤 1 — 运行完整流水线**

```bash
python pipeline.py
```

这按顺序执行四件事：
1. 从 `stories/` 中的每个故事生成 pytest 测试
2. 运行完整的 pytest 套件
3. 用 AI 分析所有失败
4. 构建并在浏览器中打开 `ai-report.html`

**步骤 2 — 查看结果**

- `ai-report.html` — AI 仪表盘：通俗易懂的解释、根本原因、修复建议、不稳定提示
- `playwright-report/` — 带有截图的传统 pytest-html 报告
- `pytest-report.json` — 原始的机器可读输出

---

## 工作流程：添加新故事并测试

当你编写了一个新故事，只想生成并运行这一个测试时使用。

**步骤 1 — 编写故事**

创建 `stories/<slug>.md`。文件名主干将成为测试函数名。

```markdown
Title: 登录 - 有效凭据

As a user, I want to log in with valid credentials so I can access the secure area.

Acceptance criteria:
- Navigate to `/login`
- Fill in username `tomsmith`
- Fill in password `SuperSecretPassword!`
- Click the Login button
- Expect redirect to `/secure`
- Expect the success flash message to contain: `You logged into a secure area!`
```

注意：
- **`Base URL:` 是可选的。** 如果省略，`generate_test.py` 使用 `test_config.yaml` 中的默认值（`environments.<default_env>.base_url`）。仅当故事针对与仓库默认值**不同**的站点时才包含 `Base URL:`。
- 验收标准中使用相对路径（`/login`，而非完整 URL）。
- slug（文件名主干）必须使用蛇形命名法：`add_remove_elements.md` → `test_add_remove_elements.py`。

**步骤 2 — 生成测试**

```bash
python generate_test.py --story <slug>.md
```

示例：
```bash
python generate_test.py --story login.md
```

这将创建 `tests/test_login.py`。检查并根据需要调整定位器。

**步骤 3 — 仅运行该测试**

```bash
python -m pytest tests/test_<slug>.py -v
```

**步骤 4 — 如果失败，获取 AI 分析**

```bash
python -m pytest tests/test_login.py -v --json-report --json-report-file=pytest-report.json
python analyze/analyze_failures.py --html
```

或者使用流水线快捷方式，一步完成步骤 2-4：

```bash
python pipeline.py --story login.md --test test_login.py
```

---

## 独立命令参考

```bash
# 生成测试
python generate_test.py                          # 所有故事
python generate_test.py --story login.md         # 单个故事

# 运行测试
python -m pytest                                 # 所有测试
python -m pytest tests/test_login.py -v          # 单个测试
python -m pytest --json-report --json-report-file=pytest-report.json  # 输出 JSON 格式

# 分析失败（需要 pytest-report.json）
python analyze/analyze_failures.py               # 仅 JSON 输出
python analyze/analyze_failures.py --html        # JSON + HTML 报告（自动打开）

# 完整流水线
python pipeline.py                               # 所有故事 + 所有测试
python pipeline.py --story login.md --test test_login.py  # 单个故事 + 单个测试

# UI 服务器
uvicorn server.server:app --port 5173
```

---

## UI 仪表盘

```bash
uvicorn server.server:app --port 5173
```

打开 `http://localhost:5173`。

**运行栏** — 触发完整流水线或单个步骤（生成 / 运行测试 / 分析），带有实时状态指示器。

**编辑器** — 编写或编辑故事和测试，支持验证、一次上传最多 5 个故事，或使用 AI 故事助手向导根据需求和预期结果构建故事。

**已保存故事 / 已生成测试** — 从侧边栏浏览、编辑、删除或运行单个故事或测试。

**运行控制台** — 逐步进度（验证 → 保存 → 生成 → 运行 → 分析 → 报告）、实时日志，以及在失败测试上的 **使用 AI 修复** 按钮，自动应用 OpenCode 生成的修复、在 `tests/.ai-backups/` 中创建备份、重新运行测试，并显示修复摘要。

**报告标签页** — 嵌入的 AI 分析报告和传统的 Playwright HTML 报告（含截图），并排显示。

---

## OpenCode 技能

本仓库附带一个 OpenCode 技能，位于 `.claude/skills/pytest-playwright/SKILL.md`。

在 OpenCode 中工作时，输入：

```
/pytest-playwright
```

这将加载该技能，并为 OpenCode 提供关于此项目的完整上下文：故事格式、测试文件约定、所有可用命令、定位器最佳实践、等待策略、POM 指南，以及用于快速定位器调试的临时探索模式。

**何时使用：**
- 编写新故事或测试文件
- 调试失败的测试
- 请 OpenCode 解释定位器或等待策略
- 获取完整流水线的帮助

---

## AI 分析工作原理

pytest 运行后，失败元数据通过 CLI 传递给 OpenCode：

- 错误消息和完整回溯
- 测试节点 ID
- stdout/stderr 日志
- 原始用户故事（用于了解意图上下文）

OpenCode 为每个失败返回结构化的 HTML 片段，包含：

1. **通俗易懂的解释** — 基于被测页面的真实行为说明可能失败的原因
2. **可能的根本原因** — 2-3 个具体的技术原因
3. **建议的测试修复** — 特定的 pytest-playwright 代码改进
4. **不稳定缓解措施** — 减少间歇性失败的方法

输出写入 `ai-analysis.json`（结构化数据）和 `ai-report.html`（样式化仪表盘）。

---

## 跨仓库工具设计

`shared_utils/` 是一个可移植的工具库，设计用于跨多个仓库、针对不同应用工作。

### 工作原理

`test_config.yaml`（每个仓库一个）声明目标应用的属性：

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

`conftest.py` 将配置注入 pytest-playwright 的内置夹具钩子（`browser_context_args`、`browser_type_launch_args`），因此 `base_url`、视口和浏览器设置自动流入每个测试 — 无需在测试文件或故事中重复配置。

### 将其添加到另一个仓库

1. 将 `shared_utils/` 复制到新仓库中。
2. 编写 `adapters/my_app_adapter.py`，实现三个必需方法：

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
        # 通过 API 或数据库创建测试夹具；返回用于清理的引用
        return {}

    def cleanup_data(self, data: dict) -> None:
        pass
```

3. 为新仓库编写 `test_config.yaml`。
4. 在 `conftest.py` 中，从 `app_adapter` 返回你的适配器 — 其余一切都继承：

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

# browser_type_launch_args、browser_context_args、auth_state
# 和 authenticated_page 夹具遵循与本仓库 conftest.py 相同的模式
```

### 共享工具集

| 模块 | 提供的功能 |
|---|---|
| `shared_utils.adapters.base.AppAdapter` | 抽象基类：`login`、`seed_data`、`cleanup_data`（必需）；`after_navigation`、`setup_context`、`on_auth_failure`（可覆盖）；`base_url`、`route`、`navigate_to`（配置派生） |
| `shared_utils.core.config_loader.load_config` | 加载 `test_config.yaml` 并从环境变量解析 `${VAR:-default}` |
| `shared_utils.core.retry.retry` | 重试可调用对象 N 次，带延迟 |
| `shared_utils.core.retry.wait_for` | 轮询条件直到为真或超时 |
| `shared_utils.core.assertions.SoftAssertions` | 收集多个失败并一次性全部抛出 |

---

## 路线图

- 多故事批量生成
- 测试到故事的逆向工程
- 随时间推移的不稳定测试评分
- 频繁失败的点击热力图
- CI 流水线集成
- 发布 AI 洞察的 Slack/Teams 机器人
