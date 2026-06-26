import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(fn: Callable[[], T], attempts: int = 3, delay: float = 0.5) -> T:
    """重试 fn 最多 attempts 次，每次间隔 delay 秒。"""
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def wait_for(condition: Callable[[], bool], timeout: float = 10.0, interval: float = 0.5) -> bool:
    """轮询 condition 直到返回 True 或超时（秒）。条件满足时返回 True。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return False
