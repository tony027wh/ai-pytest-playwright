import json
import os
import subprocess

# 超过此字符数（大约 1k tokens）的提示会获得额外超时时间，用于需要多步推理的代码生成任务。
_LONG_PROMPT_THRESHOLD = 4000
_TIMEOUT_LONG = 300   # 秒
_TIMEOUT_SHORT = 120  # 秒

# 默认模型，可通过环境变量 OPENCODE_MODEL 覆盖
_DEFAULT_MODEL = os.environ.get("OPENCODE_MODEL", "cpamc/deepseek-v4-pro")


def opencode_prompt(system_msg: str | None, user_msg: str, model: str | None = None) -> str:
    """通过 OpenCode CLI 发送提示并返回模型响应文本。

    Args:
        system_msg: 系统提示（可为 None，此时仅使用 user_msg）
        user_msg: 用户提示
        model: 模型标识符（格式: provider/model），默认使用 cpamc/deepseek-v4-pro

    Returns:
        模型返回的纯文本内容

    Raises:
        subprocess.TimeoutExpired: 超时
        subprocess.CalledProcessError: OpenCode 进程异常退出
    """
    combined = f"{system_msg}\n\n{user_msg}" if system_msg else user_msg
    timeout = _TIMEOUT_LONG if len(combined) > _LONG_PROMPT_THRESHOLD else _TIMEOUT_SHORT
    model = model or _DEFAULT_MODEL

    cmd = [
        "opencode", "run", combined,
        "--model", model,
        "--format", "json",
        "--pure",
        "--dangerously-skip-permissions",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    # 从 NDJSON 输出中提取所有 type=text 事件
    texts = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "text" and ev.get("part", {}).get("type") == "text":
            texts.append(ev["part"]["text"])

    return "".join(texts).strip()


# 向后兼容别名
claude_prompt = opencode_prompt
