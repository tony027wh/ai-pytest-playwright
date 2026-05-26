from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SoftAssertions:
    """Collect assertion failures and raise them all at the end of a test."""

    _failures: list[str] = field(default_factory=list)

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self._failures.append(message)

    def check_fn(self, fn: Callable[[], None], message: str) -> None:
        """Run fn(); if it raises, record message instead of failing immediately."""
        try:
            fn()
        except Exception as exc:
            self._failures.append(f"{message}: {exc}")

    def assert_all(self) -> None:
        if self._failures:
            joined = "\n".join(f"  - {f}" for f in self._failures)
            raise AssertionError(f"{len(self._failures)} assertion(s) failed:\n{joined}")
