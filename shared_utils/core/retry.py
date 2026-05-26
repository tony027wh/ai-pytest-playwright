import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(fn: Callable[[], T], attempts: int = 3, delay: float = 0.5) -> T:
    """Retry fn up to attempts times, sleeping delay seconds between tries."""
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def wait_for(condition: Callable[[], bool], timeout: float = 10.0, interval: float = 0.5) -> bool:
    """Poll condition until True or timeout (seconds). Returns True if met."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return False
