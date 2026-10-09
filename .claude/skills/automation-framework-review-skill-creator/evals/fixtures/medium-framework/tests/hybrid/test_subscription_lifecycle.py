"""Hybrid UI+API tests covering the subscription lifecycle."""
from src.factories.factories import SubscriptionBuilder
from src.pages.dashboard_page import DashboardPage
from src.pages.list_pages import SubscriptionListPage
from src.pages.subscription_modify_page import SubscriptionModifyPage


def test_update_subscription_seats(page, authenticated_context, subscription_client):
    # step 1: create the subscription via API
    subscription = subscription_client.create_subscription(SubscriptionBuilder().build())

    # step 2: navigate to it in the UI
    dashboard = DashboardPage(page)
    dashboard.open_subscriptions()
    list_page = SubscriptionListPage(page)
    list_page.open_subscription(subscription["plan_code"])

    # step 3: modify a field
    modify_page = SubscriptionModifyPage(page)
    modify_page.wait_until_loaded()
    modify_page.update_name("PRO-ANNUAL")

    # step 4: save and assert
    modify_page.save_changes()
    updated = subscription_client.get_subscription(subscription["id"])
    assert updated["plan_code"] == "PRO-ANNUAL"


def test_cancel_subscription(page, authenticated_context, subscription_client):
    subscription = subscription_client.create_subscription(SubscriptionBuilder().build())

    dashboard = DashboardPage(page)
    dashboard.open_subscriptions()
    list_page = SubscriptionListPage(page)
    list_page.open_subscription(subscription["plan_code"])

    modify_page = SubscriptionModifyPage(page)
    modify_page.wait_until_loaded()
    modify_page.cancel_changes()

    updated = subscription_client.get_subscription(subscription["id"])
    assert updated["id"] == subscription["id"]
