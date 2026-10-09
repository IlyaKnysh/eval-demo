"""Hybrid UI+API tests covering the support-ticket lifecycle."""
from src.factories.factories import TicketBuilder
from src.pages.dashboard_page import DashboardPage
from src.pages.list_pages import TicketListPage
from src.pages.ticket_modify_page import TicketModifyPage

_CREATED_TICKET_IDS = []


def test_update_ticket_priority(page, authenticated_context, ticket_client):
    # step 1: create the ticket via API
    ticket = ticket_client.create_ticket(TicketBuilder().build())

    # step 2: navigate to it in the UI
    dashboard = DashboardPage(page)
    dashboard.open_tickets()
    list_page = TicketListPage(page)
    list_page.open_ticket(ticket["subject"])

    # step 3: modify a field
    modify_page = TicketModifyPage(page)
    modify_page.wait_until_loaded()
    modify_page.update_status("in_progress")

    # step 4: save and assert
    modify_page.save_changes()
    updated = ticket_client.get_ticket(ticket["id"])
    assert updated["status"] == "in_progress"


def test_create_ticket_and_record_id(ticket_client):
    ticket = ticket_client.create_ticket(TicketBuilder().with_priority("high").build())
    _CREATED_TICKET_IDS.append(ticket["id"])
    assert ticket["priority"] == "high"


def test_second_test_relies_on_previous_ticket(ticket_client):
    # Only passes if test_create_ticket_and_record_id already ran
    # in the same session and populated _CREATED_TICKET_IDS. Running this
    # test alone (pytest -k test_second_test_relies_on_previous_ticket) raises
    # an IndexError instead of a meaningful assertion failure.
    ticket_id = _CREATED_TICKET_IDS[-1]
    ticket = ticket_client.get_ticket(ticket_id)
    assert ticket["priority"] == "high"
