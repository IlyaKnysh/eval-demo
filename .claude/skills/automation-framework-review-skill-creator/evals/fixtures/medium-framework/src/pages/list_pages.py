"""List/browse page objects for tickets and subscriptions."""


class TicketListPage:
    def __init__(self, page):
        self.page = page

    def open_ticket(self, ticket_subject: str):
        self.page.get_by_role("link", name=ticket_subject).click()

    def filter_by_status(self, status: str):
        self.page.get_by_role("combobox", name="Filter by status").select_option(status)

    def row_count(self) -> int:
        return self.page.get_by_test_id("ticket-row").count()


class SubscriptionListPage:
    def __init__(self, page):
        self.page = page

    def open_subscription(self, plan_code: str):
        self.page.get_by_role("link", name=plan_code).click()

    def filter_by_tier(self, tier: str):
        self.page.get_by_role("combobox", name="Filter by tier").select_option(tier)

    def row_count(self) -> int:
        return self.page.get_by_test_id("subscription-row").count()
