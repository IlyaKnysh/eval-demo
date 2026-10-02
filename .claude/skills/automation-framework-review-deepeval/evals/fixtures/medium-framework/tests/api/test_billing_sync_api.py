"""API tests for triggering third-party billing sync on a subscription.

Imports `requests` directly and makes raw HTTP calls instead of going
through SubscriptionClient (which already exists and is used correctly by
tests/api/test_subscription_api.py and the hybrid subscription tests) --
inconsistent layer usage within the same test suite. It also pulls the raw
API token straight from Config/env and passes it directly as a header,
instead of obtaining it through the typed AuthContext/User object (see
src/core/auth.py) the way most other tests do.
"""
import requests

from src.core.config import Config
from src.factories.factories import SubscriptionBuilder


def test_billing_sync_triggers_provider_call(subscription_client):
    subscription = subscription_client.create_subscription(SubscriptionBuilder().build())

    # Raw requests call bypassing SubscriptionClient/BaseApiClient.
    response = requests.post(
        f"{Config.API_BASE_URL}/subscriptions/{subscription['id']}/billing-sync",
        json={"provider_api_key": Config.INVOICING_PROVIDER_API_KEY},
        headers={"Authorization": f"Bearer {Config.API_TOKEN}"},  # raw token, bypasses AuthContext
        timeout=15,
    )
    assert response.status_code == 200
    assert response.json()["synced"] is True


def test_billing_sync_records_external_reference(subscription_client):
    subscription = subscription_client.create_subscription(SubscriptionBuilder().build())

    # Same raw-requests bypass repeated in a second test in this file.
    response = requests.post(
        f"{Config.API_BASE_URL}/subscriptions/{subscription['id']}/billing-sync",
        json={"provider_api_key": Config.INVOICING_PROVIDER_API_KEY},
        headers={"Authorization": f"Bearer {Config.API_TOKEN}"},
        timeout=15,
    )
    body = response.json()
    assert body["external_ref"] == subscription["external_ref"]
