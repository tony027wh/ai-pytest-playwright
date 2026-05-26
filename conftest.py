import pytest

from adapters.the_internet_adapter import TheInternetAdapter
from shared_utils.core.config_loader import load_config


@pytest.fixture(scope="session")
def repo_config():
    return load_config("test_config.yaml")


@pytest.fixture(scope="session")
def app_adapter(repo_config):
    return TheInternetAdapter(repo_config)


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, repo_config):
    browser_cfg = repo_config.get("browser", {})
    return {
        **browser_type_launch_args,
        "headless": browser_cfg.get("headless", True),
        "slow_mo": browser_cfg.get("slow_mo", 0),
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, repo_config, app_adapter):
    browser_cfg = repo_config.get("browser", {})
    return {
        **browser_context_args,
        "base_url": app_adapter.base_url(),
        "viewport": browser_cfg.get("viewport", {"width": 1280, "height": 720}),
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def auth_state(app_adapter, browser, repo_config):
    """Login once per session and cache storageState to disk."""
    from pathlib import Path

    state_file = Path(repo_config["auth"]["state_file"])
    state_file.parent.mkdir(parents=True, exist_ok=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    app_adapter.login(page)
    ctx.storage_state(path=str(state_file))
    ctx.close()
    return str(state_file)


@pytest.fixture
def authenticated_page(page, app_adapter):
    """Function-scoped page already in an authenticated browser context."""
    app_adapter.after_navigation(page)
    return page
