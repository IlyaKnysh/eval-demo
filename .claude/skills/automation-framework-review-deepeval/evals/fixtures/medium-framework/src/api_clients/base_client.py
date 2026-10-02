"""Shared low-level HTTP plumbing used by the *Client wrapper classes.

This is a thin composition helper, not a base-class setup chain -- the
*Client classes below compose a requests.Session rather than inheriting test
lifecycle behavior, so this does not count as a "God Base Class" (see
conftest.py fixtures for how test lifecycle/setup is actually composed).
"""
import requests


class BaseApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def set_auth_token(self, token: str) -> None:
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"


class AuthClient(BaseApiClient):
    def authenticate(self, username: str, password: str) -> str:
        response = self.session.post(
            self._url("/auth/sessions"),
            json={"username": username, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["token"]
