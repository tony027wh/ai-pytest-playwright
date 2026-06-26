import os
import re
from pathlib import Path

import yaml


def load_config(path: str | Path = "test_config.yaml") -> dict:
    """加载 test_config.yaml 并解析 ${VAR:-default} 表达式。"""
    raw = Path(path).read_text(encoding="utf-8")
    return yaml.safe_load(_resolve_env_vars(raw))


def _resolve_env_vars(text: str) -> str:
    def replace(match: re.Match) -> str:
        inner = match.group(1)
        if ":-" in inner:
            var, default = inner.split(":-", 1)
        else:
            var, default = inner, ""
        return os.environ.get(var.strip(), default.strip())

    return re.sub(r"\$\{([^}]+)\}", replace, text)
