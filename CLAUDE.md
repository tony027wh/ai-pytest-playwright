# ai-pytest-playwright

AI 驱动的 pytest-playwright 测试自动化框架。Markdown 格式的用户故事 → OpenCode 生成 Python 测试 → pytest 运行测试 → AI 分析失败。

## 命令

```bash
# 完整流水线（生成 + 测试 + 分析 + HTML 报告）
python pipeline.py

# 独立步骤
python generate_test.py                    # 从所有故事生成测试
python generate_test.py --story login.md   # 为单个故事生成测试
python -m pytest                           # 运行所有测试
python analyze/analyze_failures.py         # AI 分析（仅 JSON）
python analyze/analyze_failures.py --html  # AI 分析 + HTML 报告

# UI 服务器（http://localhost:5173）
uvicorn server.server:app --port 5173
```

## 架构

### 数据流
```
stories/*.md
    → generate_test.py (opencode 子进程)
        → tests/test_*.py
            → pytest (pytest-report.json + playwright-report/)
                → analyze/analyze_failures.py
                    → ai-analysis.json + ai-report.html
```

### 故事格式
纯英文 `.md` 文件，位于 `stories/` 目录下。文件名主干成为测试 slug：
- `stories/login.md` → `tests/test_login.py` → `def test_login(page: Page):`

```markdown
Title: 登录 - 有效凭据

Base URL: https://the-internet.herokuapp.com

As a user, I want to log in with valid credentials.

Acceptance criteria:
- Navigate to `/login`
- Fill in username `tomsmith`
- Fill in password `SuperSecretPassword!`
- Click the Login button
- Expect redirect to `/secure`
```

### pytest-json-report 格式
`analyze_failures.py` 读取 `pytest-report.json`。测试节点 ID 的格式为：
`tests/test_login.py::test_login`

通过从文件名主干去除 `test_` 前缀来提取 slug：
`test_login.py` → `login` → 加载 `stories/login.md` 作为上下文。

### 测试文件命名
- 故事：`stories/add_remove_elements.md`
- 测试文件：`tests/test_add_remove_elements.py`
- 测试函数：`def test_add_remove_elements(page: Page):`

### 报告
- `pytest-report.json` — 机器可读的 pytest 输出（分析器的输入）
- `playwright-report/` — pytest-html 传统报告（在 UI 中以 iframe 嵌入）
- `ai-analysis.json` — 每个失败的结构化 AI 分析
- `ai-report.html` + `ai-report.css` — 精美的 AI 失败仪表盘

### 服务器
FastAPI 服务器与 Node HTTP 服务器的 API 完全一致。
所有 `/api/*` 路径完全相同，因此 UI 无需修改即可工作。

AI 修复前的测试文件备份存储在 `tests/.ai-backups/` 中。

## 依赖

```
pytest
pytest-playwright
pytest-json-report
pytest-html
fastapi
uvicorn[standard]
python-dotenv
```

安装：
```bash
pip install -r requirements.txt
playwright install
```
