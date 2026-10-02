class DashboardPage:
    def __init__(self, page):
        self.page = page

    def open_accounts(self):
        self.page.get_by_role("link", name="Accounts").click()

    def open_tickets(self):
        self.page.get_by_role("link", name="Tickets").click()

    def open_subscriptions(self):
        self.page.get_by_role("link", name="Subscriptions").click()

    def search(self, query: str):
        self.page.get_by_role("searchbox", name="Global search").fill(query)
        self.page.get_by_role("button", name="Search").click()
