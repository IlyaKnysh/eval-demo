"""UI-only tests for account and ticket search/filtering.

Relies entirely on Playwright's built-in auto-waiting
(get_by_role/get_by_test_id .wait_for()/assertions) -- no time.sleep anywhere
in this file or the rest of the suite.
"""
from src.factories.factories import AccountBuilder, TicketBuilder
from src.pages.dashboard_page import DashboardPage
from src.pages.list_pages import TicketListPage


def test_search_finds_account_by_name(page, authenticated_context, account_client):
    account = account_client.create_account(AccountBuilder().with_name("Globex Test Corp").build())

    dashboard = DashboardPage(page)
    dashboard.search(account["name"])

    result = page.get_by_role("link", name=account["name"])
    result.wait_for()
    assert result.is_visible()


def test_suspended_account_shows_suspended_badge(page, authenticated_context, account_client):
    account = account_client.create_account(AccountBuilder().suspended().build())

    dashboard = DashboardPage(page)
    dashboard.search(account["name"])
    page.get_by_role("link", name=account["name"]).click()

    badge = page.get_by_test_id("account-status-badge")
    badge.wait_for()
    assert badge.inner_text() == "Suspended"


def test_filter_tickets_by_status(page, authenticated_context):
    dashboard = DashboardPage(page)
    dashboard.open_tickets()

    list_page = TicketListPage(page)
    list_page.filter_by_status("open")

    page.get_by_test_id("ticket-row").first.wait_for()
    assert list_page.row_count() > 0


def test_search_finds_ticket_by_subject(page, authenticated_context, ticket_client):
    ticket = ticket_client.create_ticket(TicketBuilder().with_subject("Cannot access invoices").build())

    dashboard = DashboardPage(page)
    dashboard.search(ticket["subject"])

    result = page.get_by_role("link", name=ticket["subject"])
    result.wait_for()
    assert result.is_visible()
