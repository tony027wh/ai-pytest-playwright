import os
import re
from abc import ABC, abstractmethod

from playwright.sync_api import BrowserContext, Page


class AppAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config

    # ── 每个仓库必须实现 ───────────────────────────────────────────────

    @abstractmethod
    def login(self, page: Page) -> None:
        """驱动登录 UI/API 流程直至完成。"""
        ...

    @abstractmethod
    def seed_data(self) -> dict:
        """创建测试夹具；返回清理所需的引用。"""
        ...

    @abstractmethod
    def cleanup_data(self, data: dict) -> None:
        """清理 seed_data 创建的所有内容。"""
        ...

    # ── 当应用需要时覆写（安全默认值 = 空操作）────────────────────────

    def after_navigation(self, page: Page) -> None:
        """关闭 Cookie 横幅、弹窗等。每次 goto 后调用。"""
        pass

    def setup_context(self, context: BrowserContext) -> None:
        """额外的上下文级别设置：模拟路由、注入请求头等。"""
        pass

    def on_auth_failure(self, page: Page) -> None:
        """检测到认证状态过期时调用。默认行为：重新登录。"""
        self.login(page)

    # ── 从配置派生（无需覆写）──────────────────────────────────────────

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
