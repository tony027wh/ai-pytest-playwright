import os
import re
from abc import ABC, abstractmethod

from playwright.sync_api import BrowserContext, Page


class AppAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    # ── Must implement per repo ────────────────────────────────────────

    @abstractmethod
    def login(self, page: Page) -> None:
        """Drive the login UI/API flow to completion."""
        ...

    @abstractmethod
    def seed_data(self) -> dict:
        """Create test fixtures; return references needed for cleanup."""
        ...

    @abstractmethod
    def cleanup_data(self, data: dict) -> None:
        """Tear down anything created by seed_data."""
        ...

    # ── Override when your app needs it (safe default = no-op) ────────

    def after_navigation(self, page: Page) -> None:
        """Dismiss cookie banners, modals, etc. Called after every goto."""
        pass

    def setup_context(self, context: BrowserContext) -> None:
        """Extra context-level setup: mock routes, inject headers, etc."""
        pass

    def on_auth_failure(self, page: Page) -> None:
        """Called when auth state is detected as stale. Default: re-login."""
        self.login(page)

    # ── Derived from config (no override needed) ───────────────────────

    def base_url(self, env: str | None = None) -> str:
        env = env or self._resolve_env()
        return self.config["environments"][env]["base_url"]

    def route(self, name: str) -> str:
        return self.config.get("routes", {}).get(name, f"/{name}")

    def navigate_to(self, page: Page, route_name: str) -> None:
        page.goto(self.base_url() + self.route(route_name))
        self.after_navigation(page)

    def _resolve_env(self) -> str:
        raw = self.config["app"]["default_env"]
        match = re.match(r"^\$\{(\w+)(?::-(.*))?\}$", raw)
        if match:
            var, default = match.group(1), match.group(2) or ""
            return os.environ.get(var, default)
        return raw
