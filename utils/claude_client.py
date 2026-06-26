import subprocess

# 超过此字符数（大约 1k tokens）的提示会获得额外超时时间，用于需要多步推理的代码生成任务。
_LONG_PROMPT_THRESHOLD = 4000
_TIMEOUT_LONG = 300   # 秒
_TIMEOUT_SHORT = 120  # 秒


def claude_prompt(system_msg: str, user_msg: str, model: str = None) -> str:
    combined = f"{system_msg}\n\n{user_msg}" if system_msg else user_msg
    timeout = _TIMEOUT_LONG if len(combined) > _LONG_PROMPT_THRESHOLD else _TIMEOUT_SHORT

    cmd = ["claude", "-p", combined]
    if model:
        cmd += ["--model", model]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()
