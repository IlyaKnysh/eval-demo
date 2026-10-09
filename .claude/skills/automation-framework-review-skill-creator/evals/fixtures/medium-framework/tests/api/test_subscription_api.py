"""API tests for the /subscriptions surface (create/read paths).

Uses SubscriptionClient consistently, unlike test_billing_sync_api.py in
this same package.
"""
from src.factories.factories import SubscriptionBuilder


def test_create_subscription_defaults_to_auto_renew(subscription_client):
    subscription = subscription_client.create_subscription(SubscriptionBuilder().build())
    assert subscription["auto_renew"] is True


def test_cancel_subscription_marks_cancelled(subscription_client):
    subscription = subscription_client.create_subscription(SubscriptionBuilder().build())
    subscription_client.cancel_subscription(subscription["id"])
    updated = subscription_client.get_subscription(subscription["id"])
    assert updated["status"] == "cancelled"
