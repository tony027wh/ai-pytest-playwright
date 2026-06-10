import subprocess

# Prompts above this character count (roughly 1k tokens) get extra time for
# code generation tasks that require multiple reasoning steps.
_LONG_PROMPT_THRESHOLD = 4000
_TIMEOUT_LONG = 300   # seconds
_TIMEOUT_SHORT = 120  # seconds


def claude_prompt(system_msg: str, user_msg: str, model: str = None) -> str:
    combined = f"{system_msg}\n\n{user_msg}" if system_msg else user_msg
    timeout = _TIMEOUT_LONG if len(combined) > _LONG_PROMPT_THRESHOLD else _TIMEOUT_SHORT

    cmd = ["claude", "-p", combined]
    if model:
        cmd += ["--model", model]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()
