"""API tests for the /accounts surface.

Uses the AccountClient wrapper consistently, unlike test_billing_sync_api.py
and test_ticket_export_api.py in this same package.
"""
from src.factories.factories import AccountBuilder


def test_create_account_returns_active_status(account_client, authenticated_context):
    account = account_client.create_account(AccountBuilder().build())
    assert account["status"] == "active"


def test_update_account_plan_tier(account_client, authenticated_context):
    account = account_client.create_account(AccountBuilder().build())
    updated = account_client.update_account(account["id"], {"plan_tier": "enterprise"})
    assert updated["plan_tier"] == "enterprise"


def test_delete_account(account_client, authenticated_context):
    account = account_client.create_account(AccountBuilder().build())
    account_client.delete_account(account["id"])
    # Executes the delete call but never asserts the account is actually
    # gone (e.g. via a 404 on get_account or a status field check) -- a
    # broken delete endpoint would still pass this test.
    account_client.get_account.__self__  # no-op access, not a real assertion
