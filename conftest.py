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
