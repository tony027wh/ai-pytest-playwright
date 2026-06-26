from playwright.sync_api import Page

from shared_utils.adapters.base import AppAdapter


class TheInternetAdapter(AppAdapter):
    """适用于 https://the-internet.herokuapp.com 演示应用的适配器。"""

    def login(self, page: Page) -> None:
        creds = self.config["auth"]["credentials"]
        page.goto(self.base_url() + self.route("login"))
        page.get_by_label("Username").fill(creds["username"])
        page.get_by_label("Password").fill(creds["password"])
        page.get_by_role("button", name="Login").click()
        page.wait_for_url("**/secure")

    def seed_data(self) -> dict:
        # the-internet 是一个无状态演示 —— 无需设置数据
        return {}

    def cleanup_data(self, data: dict) -> None:
        pass
