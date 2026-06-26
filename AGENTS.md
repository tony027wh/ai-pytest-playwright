# ai-pytest-playwright

AI 驱动的 pytest-playwright 测试框架。用户故事 `.md` → OpenCode 生成测试 → pytest 运行 → AI 分析失败。

## 常用命令

```bash
# 完整流水线
python pipeline.py
python pipeline.py --story login.md --test test_login.py

# 生成测试
python generate_test.py                      # 所有故事
python generate_test.py --story login.md     # 单个故事

# 运行测试（pytest.ini 已配置 --json-report）
python -m pytest
python -m pytest tests/test_login.py -v

# 分析失败
python analyze/analyze_failures.py           # 仅 JSON
python analyze/analyze_failures.py --html    # JSON + HTML 报告

# UI 服务器
uvicorn server.server:app --port 5173
```

## 架构核心

### 数据流
```
stories/*.md  →  generate_test.py  →  tests/test_*.py  →  pytest  →  analyze_failures.py
                                                                    →  ai-analysis.json + ai-report.html
```

### 命名约定
| 故事 | 测试文件 | 测试函数 |
|------|---------|---------|
| `stories/login.md` | `tests/test_login.py` | `def test_login(page: Page):` |
| `stories/add_remove_elements.md` | `tests/test_add_remove_elements.py` | `def test_add_remove_elements(page: Page):` |

文件名主干 = slug，蛇形命名。

### 配置驱动
`test_config.yaml` → `conftest.py` → pytest-playwright 内置夹具。`base_url`、视口、浏览器设置自动注入，测试中直接用相对路径 `page.goto("/login")`。

### AI 调用
所有 AI 调用通过 `utils/opencode_client.py` 的 `opencode_prompt(system_msg, user_msg)` → 子进程 `opencode run`。5 个调用点：
1. `generate_test.py` — 故事 → 测试代码
2. `analyze/analyze_failures.py` — 失败 → 分析报告
3. `server.py POST /api/ai/story` — 需求 → 用户故事
4. `server.py POST /api/ai/fix-test` — 失败测试 → 修复
5. `server.py POST /api/ai/fix-test` — 修复前后对比 → 摘要

模型可通过环境变量 `OPENCODE_MODEL` 覆盖，默认 `cpamc/deepseek-v4-pro`。

### 关键文件
- `test_config.yaml` — 仓库配置：环境、浏览器、认证、路由
- `conftest.py` — pytest 会话级夹具，注入配置
- `shared_utils/adapters/base.py` — 跨仓库可复用的 AppAdapter 抽象基类
- `adapters/the_internet_adapter.py` — 本仓库的具体适配器实现

## 注意事项

- `pytest.ini` 已配置 `addopts = --json-report --json-report-file=pytest-report.json --html=playwright-report/index.html --self-contained-html`，运行 `pytest` 时自动生成 JSON 和 HTML 报告
- 生成测试后会自动运行 `ast.parse` 语法检查和函数名校验
- AI 修复前会自动备份到 `tests/.ai-backups/<file>.<timestamp>.bak`
- `Base URL:` 在故事中是可选的 — 省略时使用 `test_config.yaml` 的默认值
- 项目使用 `opencode` 命令（非 `claude`），需要安装 OpenCode CLI

## 跨仓库使用

`shared_utils/` 可复制到其他仓库。只需：
1. 复制 `shared_utils/`
2. 实现 `adapters/<my_app>_adapter.py`（实现 `login`、`seed_data`、`cleanup_data`）
3. 编写 `test_config.yaml`
4. 在 `conftest.py` 中返回自定义适配器
