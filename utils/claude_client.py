import os
import secrets
import subprocess
import tempfile


def claude_prompt(system_msg: str, user_msg: str, model: str = None) -> str:
    combined = f"{system_msg}\n\n{user_msg}" if system_msg else user_msg

    if len(combined) > 4000:
        return _claude_prompt_with_file(combined, model)

    cmd = ["claude", "-p", combined]
    if model:
        cmd += ["--model", model]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout.strip()


def _claude_prompt_with_file(content: str, model: str = None) -> str:
    suffix = secrets.token_hex(4)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=f"_prompt_{suffix}.txt",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(content)
        tmp = f.name

    try:
        flag = f'--model "{model}"' if model else ""
        cmd = f"claude -p \"$(cat '{tmp}')\" {flag}"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=300
        )
        return result.stdout.strip()
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
