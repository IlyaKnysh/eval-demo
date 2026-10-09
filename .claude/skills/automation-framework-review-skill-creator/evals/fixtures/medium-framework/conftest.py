"""Fixture composition root.

Setup is composed via pytest fixtures (dependency injection) -- each test
declares exactly the fixtures it needs and pytest wires them together.
"""
import pytest
from playwright.sync_api import sync_playwright

from src.api_clients.base_client import AuthClient
from src.api_clients.clients import AccountClient, SubscriptionClient, TicketClient
from src.core.auth import AuthContext, User
from src.core.config import Config


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture
def context(browser):
    # Trace capture enabled per-context so it can be started
    # selectively on retry (see pytest_runtest_makereport hook below).
    context = browser.new_context(base_url=Config.BASE_URL)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    context.close()


@pytest.fixture
def page(context):
    page = context.new_page()
    yield page


@pytest.fixture
def auth_client():
    return AuthClient(Config.API_BASE_URL)


@pytest.fixture
def account_client(auth_client):
    client = AccountClient(Config.API_BASE_URL)
    return client


@pytest.fixture
def ticket_client():
    return TicketClient(Config.API_BASE_URL)


@pytest.fixture
def subscription_client():
    return SubscriptionClient(Config.API_BASE_URL)


@pytest.fixture
def default_user() -> User:
    return User(username=Config.ADMIN_USERNAME, password=Config.ADMIN_PASSWORD)


@pytest.fixture
def authenticated_context(page, account_client, default_user):
    """Logs the default admin user into both UI and API layers.

    Consumers get a typed AuthContext/User rather than a raw token string
    (see src/core/auth.py). Most tests depend on this fixture; a few
    API-only tests bypass it.
    """
    ctx = AuthContext(page, account_client)
    ctx.login_as(default_user)
    return ctx


@pytest.fixture(autouse=True)
def _capture_trace_on_retry(request, context):
    """Saves the Playwright trace only when a test is on a retry attempt,
    keeping healthy first-attempt runs lightweight while still giving a full
    trace to inspect for anything pytest-rerunfailures had to retry."""
    yield
    rerun_count = getattr(request.node, "execution_count", 1)
    if rerun_count > 1 or request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        context.tracing.stop(path=f"traces/{request.node.name}.zip")
    else:
        context.tracing.stop()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
