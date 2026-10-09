"""Hybrid UI+API tests covering the account lifecycle end to end.

Every test below re-composes the same ~4-step sequence inline (create account
via API -> open account in UI -> modify a field -> save and assert), instead
of calling a shared `create_and_open_account(...)` / `modify_and_save(...)`
style step function.
"""
from src.factories.factories import AccountBuilder
from src.pages.account_modify_page import AccountModifyPage
from src.pages.dashboard_page import DashboardPage


def test_update_account_name(page, authenticated_context, account_client):
    # step 1: create the account via API
    account = account_client.create_account(AccountBuilder().build())

    # step 2: navigate to it in the UI
    dashboard = DashboardPage(page)
    dashboard.open_accounts()
    page.get_by_role("link", name=account["name"]).click()

    # step 3: modify a field
    modify_page = AccountModifyPage(page)
    modify_page.wait_until_loaded()
    modify_page.update_name("Acme Renamed Account")

    # step 4: save and assert
    modify_page.save_changes()
    updated = account_client.get_account(account["id"])
    assert updated["name"] == "Acme Renamed Account"


def test_update_account_status(page, authenticated_context, account_client):
    # step 1: create the account via API
    account = account_client.create_account(AccountBuilder().build())

    # step 2: navigate to it in the UI
    dashboard = DashboardPage(page)
    dashboard.open_accounts()
    page.get_by_role("link", name=account["name"]).click()

    # step 3: modify a field
    modify_page = AccountModifyPage(page)
    modify_page.wait_until_loaded()
    modify_page.update_status("suspended")

    # step 4: save and assert
    modify_page.save_changes()
    updated = account_client.get_account(account["id"])
    assert updated["status"] == "suspended"


def test_delete_account_removes_from_list(page, authenticated_context, account_client):
    account = account_client.create_account(AccountBuilder().build())
    account_client.delete_account(account["id"])

    dashboard = DashboardPage(page)
    dashboard.open_accounts()
    dashboard.search(account["name"])

    # Executes steps but never asserts anything -- a regression here (e.g.
    # deleted account still showing in search results) would pass silently.
    page.get_by_test_id("search-results").wait_for()
