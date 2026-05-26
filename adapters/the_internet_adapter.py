from playwright.sync_api import Page

from shared_utils.adapters.base import AppAdapter


class TheInternetAdapter(AppAdapter):
    """Adapter for https://the-internet.herokuapp.com demo app."""

    def login(self, page: Page) -> None:
        creds = self.config["auth"]["credentials"]
        page.goto(self.base_url() + self.route("login"))
        page.get_by_label("Username").fill(creds["username"])
        page.get_by_label("Password").fill(creds["password"])
        page.get_by_role("button", name="Login").click()
        page.wait_for_url("**/secure")

    def seed_data(self) -> dict:
        # the-internet is a stateless demo — no data setup needed
        return {}

    def cleanup_data(self, data: dict) -> None:
        pass
