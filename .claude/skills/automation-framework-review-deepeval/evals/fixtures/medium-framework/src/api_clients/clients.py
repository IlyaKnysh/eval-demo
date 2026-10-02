"""API client wrapper classes for the accounts, tickets, and subscriptions
surfaces. Each wraps src.api_clients.base_client.BaseApiClient's shared
requests.Session/URL-building plumbing behind a domain-specific *Client class.

Consistently suffixed *Client, matching the *Page / test_*.py conventions
used elsewhere in this repo.
"""
from src.api_clients.base_client import BaseApiClient


class AccountClient(BaseApiClient):
    """Wrapper around the /accounts API surface."""

    def create_account(self, payload: dict) -> dict:
        response = self.session.post(self._url("/accounts"), json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_account(self, account_id: str) -> dict:
        response = self.session.get(self._url(f"/accounts/{account_id}"), timeout=10)
        response.raise_for_status()
        return response.json()

    def update_account(self, account_id: str, payload: dict) -> dict:
        response = self.session.patch(
            self._url(f"/accounts/{account_id}"), json=payload, timeout=10
        )
        response.raise_for_status()
        return response.json()

    def delete_account(self, account_id: str) -> None:
        response = self.session.delete(self._url(f"/accounts/{account_id}"), timeout=10)
        response.raise_for_status()


class TicketClient(BaseApiClient):
    """Wrapper around the /tickets API surface."""

    def create_ticket(self, payload: dict) -> dict:
        response = self.session.post(self._url("/tickets"), json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_ticket(self, ticket_id: str) -> dict:
        response = self.session.get(self._url(f"/tickets/{ticket_id}"), timeout=10)
        response.raise_for_status()
        return response.json()

    def export_ticket(self, ticket_id: str) -> bytes:
        response = self.session.get(
            self._url(f"/tickets/{ticket_id}/export"), timeout=15
        )
        response.raise_for_status()
        return response.content

    def close_ticket(self, ticket_id: str) -> dict:
        response = self.session.post(self._url(f"/tickets/{ticket_id}/close"), timeout=10)
        response.raise_for_status()
        return response.json()


class SubscriptionClient(BaseApiClient):
    """Wrapper around the /subscriptions API surface, including billing sync."""

    def create_subscription(self, payload: dict) -> dict:
        response = self.session.post(self._url("/subscriptions"), json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_subscription(self, subscription_id: str) -> dict:
        response = self.session.get(
            self._url(f"/subscriptions/{subscription_id}"), timeout=10
        )
        response.raise_for_status()
        return response.json()

    def trigger_billing_sync(self, subscription_id: str, provider_api_key: str) -> dict:
        response = self.session.post(
            self._url(f"/subscriptions/{subscription_id}/billing-sync"),
            json={"provider_api_key": provider_api_key},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def cancel_subscription(self, subscription_id: str) -> None:
        response = self.session.post(
            self._url(f"/subscriptions/{subscription_id}/cancel"), timeout=10
        )
        response.raise_for_status()
