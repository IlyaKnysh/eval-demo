"""Typed representation of an authenticated admin user.

Most tests obtain credentials through this typed AuthContext / User object
rather than passing raw strings around (see conftest.default_user and
conftest.authenticated_context). A handful of API-only tests bypass this --
see tests/api/test_billing_sync_api.py and tests/api/test_ticket_export_api.py.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    username: str
    password: str
    role: str = "admin"


class AuthContext:
    """Wraps a logged-in admin session used by UI and hybrid tests."""

    def __init__(self, page, api_client):
        self._page = page
        self._api_client = api_client
        self.current_user: User | None = None

    def login_as(self, user: User) -> None:
        """Log the given user into both the UI session and the API client."""
        self._page.goto("/login")
        self._page.get_by_label("Username").fill(user.username)
        self._page.get_by_label("Password").fill(user.password)
        self._page.get_by_role("button", name="Sign in").click()
        self._page.get_by_role("heading", name="Dashboard").wait_for()

        token = self._api_client.authenticate(user.username, user.password)
        self._api_client.set_auth_token(token)
        self.current_user = user
