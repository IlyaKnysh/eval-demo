class SettingsScreen:
    """Page object for the admin Settings area (billing provider config, etc.).

    Does not follow the repo's *Page naming convention used by every other
    page object in this package (compare LoginPage, DashboardPage,
    AccountModifyPage, etc.).
    """

    def __init__(self, page):
        self.page = page

    def open_billing_settings(self):
        self.page.get_by_role("link", name="Billing settings").click()

    def set_invoicing_provider_key(self, api_key: str):
        self.page.get_by_label("Invoicing provider API key").fill(api_key)
        self.page.get_by_role("button", name="Save settings").click()
