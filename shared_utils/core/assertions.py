from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SoftAssertions:
    """收集断言失败信息，并在测试结束时统一抛出。"""

    _failures: list[str] = field(default_factory=list)

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self._failures.append(message)

    def check_fn(self, fn: Callable[[], None], message: str) -> None:
        """执行 fn()；如果抛出异常，则记录 message 而不是立即失败。"""
        try:
            fn()
        except Exception as exc:
            self._failures.append(f"{message}: {exc}")

    def assert_all(self) -> None:
        if self._failures:
            joined = "\n".join(f"  - {f}" for f in self._failures)
            raise AssertionError(f"{len(self._failures)} 个断言失败:\n{joined}")
