import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.opencode_client import opencode_prompt as claude_prompt
from utils.test_helpers import collect_failed_tests, config_base_url, nodeid_to_slug

REPORT_CSS = """
:root {
  color-scheme: dark;
  --bg: #020617;
  --bg-elevated: #020617;
  --bg-soft: #020617;
  --border-subtle: rgba(31,41,55,0.9);
  --border-accent: rgba(56,189,248,0.7);
  --text-main: #e5e7eb;
  --text-muted: #9ca3af;
  --pill-bg: rgba(15,118,110,0.15);
  --pill-border: rgba(45,212,191,0.35);
  --pill-text: #a5f3fc;
  --status-bg: radial-gradient(circle at top, rgba(248,113,113,0.15), rgba(15,23,42,0.9));
  --status-border: rgba(248,113,113,0.7);
  --status-text: #fecaca;
  --accent: #38bdf8;
  --accent-soft: rgba(56,189,248,0.12);
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0;
  padding: 0;
  background:
    radial-gradient(circle at top left, #1d293b 0, #020617 45%, #000 100%);
  color: var(--text-main);
}

.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-shell::before {
  content: "";
  position: fixed;
  inset: 0 0 auto;
  height: 3px;
  background: linear-gradient(90deg,
    #22d3ee,
    #a855f7,
    #f97316,
    #22d3ee);
  background-size: 300% 100%;
  animation: shimmer 9s linear infinite;
  z-index: 50;
}

@keyframes shimmer {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

header {
  padding: 1.4rem 2.2rem 1.3rem;
  background: rgba(15,23,42,0.95);
  border-bottom: 1px solid #1f2937;
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left h1 {
  margin: 0;
  font-size: 1.55rem;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.header-logo {
  width: 26px;
  height: 26px;
  border-radius: 10px;
  background: radial-gradient(circle at 20% 0%, #22d3ee, #4f46e5 40%, #0f172a 100%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 18px rgba(56,189,248,0.6);
  flex-shrink: 0;
}

.header-logo span {
  font-size: 0.85rem;
  font-weight: 700;
  color: #0b1120;
}

.header-left p {
  margin: 0.3rem 0 0;
  color: var(--text-muted);
  font-size: 0.88rem;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.2rem;
}

.tagline {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.13em;
  color: #a5b4fc;
}

.badge-chip {
  border-radius: 999px;
  padding: 0.25rem 0.7rem;
  font-size: 0.7rem;
  border: 1px solid rgba(148,163,184,0.7);
  background: rgba(15,23,42,0.9);
  color: #cbd5f5;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #22c55e;
}

main {
  padding: 1.7rem 2.2rem 3rem;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.summary {
  margin-bottom: 1.7rem;
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.pill {
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  background: var(--pill-bg);
  border: 1px solid var(--pill-border);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--pill-text);
}

.test {
  background: radial-gradient(circle at top left,
    rgba(15,23,42,0.9),
    rgba(2,6,23,1));
  border-radius: 1rem;
  padding: 1.15rem 1.3rem 1.25rem;
  margin-bottom: 1.1rem;
  border: 1px solid var(--border-subtle);
  box-shadow:
    0 18px 40px rgba(0,0,0,0.7),
    0 0 0 1px rgba(15,23,42,1);
  transition:
    transform 0.16s ease,
    box-shadow 0.16s ease,
    border-color 0.16s ease,
    background 0.16s ease;
  position: relative;
  overflow: hidden;
}

.test::before {
  content: "";
  position: absolute;
  inset: -40%;
  background:
    radial-gradient(circle at 0% 0%, rgba(56,189,248,0.12), transparent 55%),
    radial-gradient(circle at 100% 0%, rgba(129,140,248,0.16), transparent 55%);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.test:hover {
  transform: translateY(-2px);
  border-color: var(--border-accent);
  box-shadow:
    0 22px 52px rgba(15,23,42,0.9),
    0 0 0 1px rgba(56,189,248,0.4);
}

.test:hover::before {
  opacity: 1;
}

.test-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.2rem;
}

.test h2 {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
}

.badge-status {
  border-radius: 999px;
  padding: 0.25rem 0.7rem;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: 1px solid var(--status-border);
  background: var(--status-bg);
  color: var(--status-text);
}

.meta {
  margin: 0;
  padding: 0;
  font-size: 0.82rem;
  color: var(--text-muted);
}

.meta span {
  color: var(--text-main);
}

.details {
  margin-top: 0.75rem;
}

summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--accent);
  font-size: 0.9rem;
  list-style: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

summary::-webkit-details-marker {
  display: none;
}

summary::before {
  content: "▸";
  display: inline-block;
  margin-right: 0.2rem;
  transition: transform 0.15s ease;
  font-size: 0.8rem;
  color: var(--accent);
}

details[open] summary::before {
  transform: rotate(90deg);
}

.analysis {
  margin-top: 0.55rem;
  padding: 0.8rem 0.85rem;
  border-radius: 0.75rem;
  background: rgba(15,23,42,0.96);
  border: 1px solid rgba(31,41,55,0.9);
  font-size: 0.86rem;
  line-height: 1.45;
}

.analysis h3 {
  margin: 0.35rem 0 0.15rem;
  font-size: 0.95rem;
  color: #e5e7eb;
}

.analysis p {
  margin: 0.2rem 0 0.45rem;
  color: #cbd5e1;
}

.analysis ul,
.analysis ol {
  margin: 0.25rem 0 0.45rem 1.1rem;
  padding-left: 0.4rem;
}

.analysis li {
  margin-bottom: 0.15rem;
}

.analysis code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.82rem;
  background: rgba(15,23,42,0.9);
  padding: 0.1rem 0.25rem;
  border-radius: 0.3rem;
  border: 1px solid rgba(15,118,110,0.5);
}

.analysis pre {
  white-space: pre-wrap;
  background: rgba(15,23,42,0.9);
  border-radius: 0.5rem;
  padding: 0.6rem 0.7rem;
  border: 1px solid #1f2937;
  overflow-x: auto;
  font-size: 0.8rem;
}

@media (max-width: 700px) {
  header {
    padding: 1.1rem 1.4rem;
    flex-direction: column;
    align-items: flex-start;
  }
  main {
    padding: 1.3rem 1.4rem 2.4rem;
  }
}
"""


def build_html(analyses: list) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = []
    for a in analyses:
        sections.append(f"""
    <section class="test">
      <div class="test-header">
        <h2>{a['title']}</h2>
        <span class="badge-status">{a.get('status', 'unknown')}</span>
      </div>
      <p class="meta"><span>项目:</span> {a.get('project', 'n/a')}</p>
      <details open class="details">
        <summary>AI 分析</summary>
        <div class="analysis">
          {a['analysis']}
        </div>
      </details>
    </section>
""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>AI Pytest 失败分析报告</title>
  <link rel="stylesheet" href="ai-report.css" />
</head>
<body>
  <div class="app-shell">
    <header>
      <div class="header-left">
        <div class="header-logo"><span>AI</span></div>
        <div>
          <h1>AI Pytest 失败分析报告</h1>
          <p>运行洞察生成于 {now}</p>
        </div>
      </div>
      <div class="header-right">
        <div class="tagline">智能测试分类</div>
        <div class="badge-chip">
          <span class="badge-dot"></span>
          AI 助手已启用
        </div>
      </div>
    </header>

    <main>
      <div class="summary">
        <div class="pill">已分析的失败测试: {len(analyses)}</div>
        <div class="pill">pytest JSON → AI 洞察</div>
      </div>

      {"".join(sections)}
    </main>
  </div>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="使用 AI 分析 pytest 测试失败原因")
    parser.add_argument("--html", action="store_true", help="同时生成 HTML 报告")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    report_path = project_root / "pytest-report.json"

    if not report_path.exists():
        print("未找到 pytest-report.json，请先运行 pytest。", file=sys.stderr)
        sys.exit(1)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    failed_tests = collect_failed_tests(report.get("tests", []))
    app_base_url = config_base_url()
    analyses = []

    for test in failed_tests:
        nodeid = test["nodeid"]
        slug = nodeid_to_slug(nodeid)

        story_context = ""
        story_path = project_root / "stories" / f"{slug}.md"
        if story_path.exists():
            story_text = story_path.read_text(encoding="utf-8")
            story_context = f"\n\n相关用户故事（包含 Base URL 和验收标准）:\n{story_text}"

        prompt = f"""你是一名资深 QA 工程师，专攻 Playwright。

被测应用地址:
{app_base_url}

测试用例: {nodeid}
总体状态: {test['outcome']}

错误信息:
{test['crash_message'] or 'N/A'}

完整回溯:
{test['longrepr'] or 'N/A'}
{story_context}

请利用你对这个演示应用的了解以及提供的 Base URL 和故事详情，将你的回答建立在该页面的真实行为之上。

任务:
请仅返回 HTML 片段作为答案（不要包含 <html> 或 <body> 标签）。
使用标题（<h3>）、段落（<p>）、有序/无序列表（<ol>、<ul>）以及 <pre><code> 展示代码。
不要使用 Markdown，不要包含反引号。

内容要求:
1. 一个简短标题“通俗易懂的解释”和一个段落，说明该测试可能失败的原因，尽可能结合给定路径对应页面的实际行为进行推断。

2. 一个标题“可能的根本原因”，包含 2-3 个项目的列表（可用无序或有序列表）。基于被测页面的真实情况给出合理的失败原因。

3. 一个标题“建议的测试修复方案”，包含 2 个具体的 pytest-playwright 修复思路，使测试与被测页面的真实行为保持一致。

4. 一个标题“降低不稳定性的建议”，包含 1-2 个让该测试更稳定的建议。"""

        analysis_html = claude_prompt(None, prompt)
        analyses.append({
            "title": nodeid,
            "project": "pytest",
            "status": test["outcome"],
            "analysis": analysis_html,
        })
        print(f"已分析: {nodeid}")

    json_path = project_root / "ai-analysis.json"
    json_path.write_text(json.dumps(analyses, indent=2), encoding="utf-8")
    print(f"AI 分析结果已保存至: ai-analysis.json")

    if not failed_tests:
        print("报告中未发现失败的测试。")

    if args.html:
        css_path = project_root / "ai-report.css"
        css_path.write_text(REPORT_CSS, encoding="utf-8")

        html = build_html(analyses)
        html_path = project_root / "ai-report.html"
        html_path.write_text(html, encoding="utf-8")
        print(f"HTML 报告已写入: ai-report.html")

        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", str(html_path)], check=True)
            elif system == "Windows":
                subprocess.run(["start", str(html_path)], shell=True, check=True)
            else:
                subprocess.run(["xdg-open", str(html_path)], check=True)
        except Exception as e:
            print(f"警告: 无法自动打开报告: {e}", file=sys.stderr)
            print(f"请手动打开: {html_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
