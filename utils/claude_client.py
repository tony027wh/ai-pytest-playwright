import subprocess


def claude_prompt(system_msg: str, user_msg: str, model: str = None) -> str:
    combined = f"{system_msg}\n\n{user_msg}" if system_msg else user_msg
    timeout = 300 if len(combined) > 4000 else 120

    cmd = ["claude", "-p", combined]
    if model:
        cmd += ["--model", model]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout.strip()
